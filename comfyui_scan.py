#!/usr/bin/env python3
"""
ComfyUI 批量扫描 v3
流程: 测活+详情一步完成 → 输出md报告
用法: python3 comfyui_scan.py [-f csv] [-w 并发] [-t 超时]
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


def check_and_detail(srv, timeout=6, detail_timeout=8):
    """测活 + 详情采集一步完成"""
    base = srv["url"]
    r = {"url":base, "host":srv["host"], "ip":srv["ip"], "port":srv["port"],
         "ok":False, "error":None,
         "comfyui":"", "gpu_raw":"", "gpu_simple":"",
         "gpu_vram_fmt":"", "gpu_free_fmt":"",
         "ram_fmt":"", "ram_free_fmt":"",
         "models":[], "loras":[], "lora_count":0, "clips":[], "vaes":[], "workflows":[],
         "has_history":False, "manager":False, "custom_nodes":0}

    # ---- 测活 ----
    try:
        s, _, bd = fetch(f"{base}/system_stats", timeout)
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

    # ---- 详情采集（顺序执行，外层已用200并发覆盖，无需嵌套线程池）----
    def _quick_fetch(path, default=None):
        try:
            s, _, bd = fetch(f"{base}{path}", min(detail_timeout, 5))
            if s == 200:
                data = json.loads(bd)
                return data
        except: pass
        return default

    def _fetch_node_list(nt, fld):
        try:
            s, _, bd = fetch(f"{base}/object_info/{nt}", detail_timeout)
            if s == 200:
                inp = json.loads(bd).get(nt, {}).get("input", {}).get("required", {})
                return extract_names(inp.get(fld, []))
        except: pass
        return []

    # 历史
    hist_data = _quick_fetch("/history?max_items=1", {})
    r["has_history"] = isinstance(hist_data, dict) and len(hist_data) > 0

    # 模型（去重用 set，性能优于 list 线性查找）
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
    models_set = set()
    for nt, fld in MODEL_LOADERS:
        for n in _fetch_node_list(nt, fld):
            models_set.add(n)
    r["models"] = sorted(models_set)

    # LoRA
    lora_set = set()
    for nt in ("LoraLoader", "LoraLoaderModelOnly"):
        for n in _fetch_node_list(nt, "lora_name"):
            lora_set.add(n)
    r["lora_count"] = len(lora_set)
    r["loras"] = sorted(lora_set)[:10]

    # CLIP / VAE
    r["clips"] = _fetch_node_list("CLIPLoader", "clip_name")
    r["vaes"]  = _fetch_node_list("VAELoader", "vae_name")

    # Manager
    mgr_data = _quick_fetch("/customnode/installed")
    if isinstance(mgr_data, dict):
        r["manager"] = "ComfyUI-Manager" in mgr_data
        r["custom_nodes"] = len(mgr_data)
    else:
        r["manager"] = False
        r["custom_nodes"] = 0

    # Workflows
    wf_data = _quick_fetch("/api/userdata?dir=workflows")
    if isinstance(wf_data, list):
        r["workflows"] = [str(w) for w in wf_data if isinstance(w, str)]
    else:
        r["workflows"] = []

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
        cn = str(x.get("custom_nodes", 0)) if x.get("custom_nodes") else ""
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
    alive_sorted = sorted(alive, key=lambda x: (gpu_rank(x.get("gpu_simple", "")), vram_val(x)), reverse=True)

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
            cn = str(x.get("custom_nodes", 0))
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
            f.write(f"- **自定义节点数**: {x.get('custom_nodes', 0)}\n")

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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-f","--file", default=DEFAULT_CSV)
    ap.add_argument("-w","--workers", type=int, default=200)
    ap.add_argument("-t","--timeout", type=int, default=8)
    ap.add_argument("--detail-timeout", type=int, default=10)
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


if __name__ == "__main__":
    main()
