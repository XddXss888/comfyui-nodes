#!/usr/bin/env python3
"""
扫描 report.md 中的所有 ComfyUI 节点，从每个节点提取最近 10 条成功完成的历史工作流。
每个节点一个文件夹，包含工作流 JSON 文件和 report.md。

用法: python3 scan_workflows.py [report.md路径] [输出目录]
"""

import json
import os
import re
import ssl
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

REPORT_PATH = os.path.join(SCRIPT_DIR, "report.md")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "workflow")
MAX_WORKFLOWS = 10
REQUEST_TIMEOUT = 30
RETRY_COUNT = 2
MAX_WORKERS = 30

os.makedirs(OUTPUT_DIR, exist_ok=True)

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE


def sanitize_name(addr):
    name = addr.replace("https://", "").replace("http://", "")
    name = re.sub(r"[^\w\-.]", "_", name)
    return name


def parse_report(report_path=None):
    path = report_path or REPORT_PATH
    with open(path, "r") as f:
        content = f.read()
    sections = re.split(r"\n### \d+\. ", content)[1:]
    nodes = []
    for sec in sections:
        m = re.match(r"(.+)", sec)
        if not m:
            continue
        addr = m.group(1).strip()

        # GPU: 匹配 "**GPU**: XXX" 格式，不要求括号后缀
        gpu_m = re.search(r"\*\*GPU\*\*:\s*(.+?)(?:\s*\(|$)", sec)
        gpu = gpu_m.group(1).strip() if gpu_m else ""

        # 显存: 匹配整数 GB，也处理 "—" (CPU模式)
        vram_m = re.search(r"\*\*显存\*\*:\s*(\d+)\s*GB", sec)
        vram = int(vram_m.group(1)) if vram_m else 0

        # 空闲显存
        free_m = re.search(r"空闲\s*(\d+)\s*GB", sec)
        free = int(free_m.group(1)) if free_m else 0

        # 内存: 分离总量和空闲（非回溯正则，直接匹配到左括号前）
        mem_total = ""
        mem_free = ""
        mem_m = re.search(r"\*\*内存\*\*:\s*([^(]+)(?:\s*\(空闲\s*([^)]+)\))?", sec)
        if mem_m:
            mem_total = mem_m.group(1).strip()
            mem_free = (mem_m.group(2) or "").strip()

        ver_m = re.search(r"\*\*版本\*\*:\s*(.+)", sec)
        ver = ver_m.group(1).strip() if ver_m else ""

        # 历史: 统一检测 "有" 或 ✓
        has_history = bool(re.search(r"\*\*历史\*\*:\s*(有|✓)", sec))

        nodes.append({
            "addr": addr, "gpu": gpu, "vram": vram, "free": free,
            "mem_total": mem_total, "mem_free": mem_free,
            "ver": ver, "has_history": has_history
        })
    return nodes


def fix_truncated_json(raw):
    """修复被截断的 JSON——正确处理字符串内的转义和 Unicode"""
    depth = 0
    last_entry_end = 0
    in_str = False
    esc = False
    for i, ch in enumerate(raw):
        if esc:
            esc = False
            continue
        if ch == "\\":
            esc = True
            continue
        if ch == '"' and not esc:
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 1:
                last_entry_end = i + 1
    if last_entry_end > 0:
        return True, raw[:last_entry_end] + "}"
    # 如果 depth 从未到 1，尝试让 json.loads 一次就能解析
    # 可能是完整的 JSON（不需要修复）
    return False, raw


def build_urls(addr, path):
    """返回待尝试的 URL 列表"""
    addr = addr.strip()
    if addr.startswith("https://"):
        return [f"{addr.rstrip('/')}{path}"]
    elif addr.startswith("http://"):
        return [f"{addr.rstrip('/')}{path}"]
    else:
        return [f"https://{addr}{path}", f"http://{addr}{path}"]


def try_fetch(url):
    req = urllib.request.Request(url)
    try:
        if url.startswith("https"):
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=ssl_ctx) as resp:
                return resp.read()
        else:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                return resp.read()
    except (urllib.error.URLError, urllib.error.HTTPError, UnicodeDecodeError, OSError) as e:
        return None


def fetch_history(addr):
    """返回 history dict 或 None"""
    urls = build_urls(addr, "/history")
    for retry in range(RETRY_COUNT):
        for url in urls:
            raw_bytes = try_fetch(url)
            if raw_bytes is None:
                continue
            raw = raw_bytes.decode("utf-8", errors="replace")

            # 先尝试直接解析
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass

            # 尝试修复截断
            _, fixed = fix_truncated_json(raw)
            try:
                return json.loads(fixed)
            except json.JSONDecodeError:
                pass

        if retry < RETRY_COUNT - 1:
            time.sleep(1)
    return None


def classify_workflow(wf):
    types = set(v.get("class_type", "") for v in wf.values())
    video_io = {"VHS_VideoCombine", "CreateVideo", "SaveVideo", "VHS_LoadVideo", "ImageOnlyLoadVideo", "VideoCombine"}
    load_img = "LoadImage" in types
    wan_cls = [t for t in types if "Wan" in t or "wan" in t.lower()]
    flux_cls = [t for t in types if "Flux" in t or "Klein" in t or "flux" in t.lower()]
    qwen_cls = [t for t in types if "Qwen" in t or "qwen" in t.lower()]
    zimg_cls = [t for t in types if "ZImage" in t or "z_image" in t.lower()]
    ideogram_cls = [t for t in types if "Ideogram" in t or "ideogram" in t.lower()]
    hidream_cls = [t for t in types if "Hidream" in t or "hidream" in t.lower()]
    sdxl_cls = [t for t in types if "KSampler" in t and not wan_cls and not flux_cls and not qwen_cls]
    upscale_cls = [t for t in types if "Upscale" in t or "SeedVR" in t or "RIFE" in t]
    audio_cls = [t for t in types if "TTS" in t or "Audio" in t]
    gen = flux_cls or qwen_cls or zimg_cls or sdxl_cls or ideogram_cls or hidream_cls
    has_video = bool(video_io & types)

    if wan_cls and not load_img: return "文生视频"
    if wan_cls and load_img: return "图生视频"
    if upscale_cls and has_video: return "视频超分/处理"
    if upscale_cls and load_img: return "图片超分"
    if load_img and gen: return "图生图"
    if not load_img and gen: return "文生图"
    if has_video: return "视频编辑"
    if load_img and "SaveImage" in types: return "图片编辑"
    if audio_cls: return "音频生成"
    if "SaveStringKJ" in types or "Painter" in types: return "其他/工具"
    return "其他"


def extract_models(wf):
    models = set()
    skip = {"default", "cpu", "gpu", "cuda:0", "auto", "AUTO", "sdpa", "native", "cudaMallocAsync"}
    for node in wf.values():
        for k, v in node.get("inputs", {}).items():
            if isinstance(v, str) and v.endswith((".safetensors", ".ckpt", ".pt", ".pth", ".gguf", ".sft")):
                if v not in skip and not v.startswith("bbox/"):
                    models.add(v)
    return sorted(models)


def extract_node_prompts(wf):
    texts = []
    for node in wf.values():
        ct = node.get("class_type", "")
        for k, v in node.get("inputs", {}).items():
            if isinstance(v, str) and len(v) > 10 and k in ("text", "prompt", "positive", "negative"):
                texts.append(f"[{ct}::{k}] {v[:200]}")
    return texts


FORCE_SCAN = False  # 将被 main() 中的命令行参数覆盖


def should_skip(node_dir, node):
    """已有报告且包含工作流列表则跳过（增量扫描），--force 可覆盖"""
    if FORCE_SCAN:
        return False
    report_file = os.path.join(node_dir, "report.md")
    if not os.path.exists(report_file):
        return False
    try:
        with open(report_file, "r") as f:
            content = f.read()
        if "## 工作流列表" in content:
            return True
    except:
        pass
    return False


def process_node(node, idx, total):
    """返回 (addr, result_str) 而不是直接 print，避免并发输出混乱"""
    addr = node["addr"]
    name = sanitize_name(addr)
    node_dir = os.path.join(OUTPUT_DIR, name)

    # 增量扫描：跳过已有完整报告的节点
    if should_skip(node_dir, node):
        return f"[{idx}/{total}] {addr} ⏭️ 已有报告，跳过"

    history = fetch_history(addr)
    if history is None:
        return f"[{idx}/{total}] {addr} ❌ 不可达"

    total_records = len(history)
    completed = []
    for pid, entry in history.items():
        status = entry.get("status", {})
        if status.get("completed"):
            prompt_data = entry.get("prompt", [])
            if len(prompt_data) > 2:
                completed.append((pid, prompt_data))

    # 格式化显存字段：CPU 节点（显存=0）显示 — 而非 "0 GB"
    vram_str = f"{node['vram']} GB" if node['vram'] > 0 else "—"
    free_str = f"{node['free']} GB" if node['free'] > 0 else "—"

    if not completed:
        # 统一格式：即使无工作流也用标准格式
        os.makedirs(node_dir, exist_ok=True)
        report_lines = [
            f"# {addr}",
            "",
            f"**GPU**: {node['gpu']} | **显存**: {vram_str} | **空闲**: {free_str}",
            f"**内存**: {node['mem_total']} (空闲 {node['mem_free']})" if node['mem_total'] else f"**内存**: —",
            f"**版本**: {node['ver']}",
            f"**ComfyUI报告历史**: {'有' if node['has_history'] else '无'}",
            f"**扫描时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 工作流列表",
            "",
            f"**历史总数**: {total_records} | **成功**: 0",
            "",
        ]
        with open(os.path.join(node_dir, "report.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
        return f"[{idx}/{total}] {addr} — {total_records}条记录 / 0成功"

    completed = completed[-MAX_WORKFLOWS:]
    os.makedirs(node_dir, exist_ok=True)

    report_lines = [
        f"# {addr}",
        "",
        f"**GPU**: {node['gpu']} | **显存**: {vram_str} | **空闲**: {free_str}",
        f"**内存**: {node['mem_total']} (空闲 {node['mem_free']})" if node['mem_total'] else f"**内存**: —",
        f"**版本**: {node['ver']}",
        f"**ComfyUI报告历史**: {'有' if node['has_history'] else '无'}",
        f"**扫描时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**历史总数**: {total_records} | **成功**: {len(completed)}",
        "",
        "## 工作流列表",
        "",
    ]

    for i, (pid, pd) in enumerate(completed, 1):
        wf = pd[2]
        wf_type = classify_workflow(wf)
        models = extract_models(wf)
        texts = extract_node_prompts(wf)

        fn = f"workflow_{i:02d}.json"
        with open(os.path.join(node_dir, fn), "w", encoding="utf-8") as f:
            json.dump(wf, f, indent=2, ensure_ascii=False)

        report_lines.append(f"### {i}. {fn}")
        report_lines.append(f"- **Prompt ID**: `{pid}`")
        report_lines.append(f"- **类型**: {wf_type}")
        report_lines.append(f"- **节点数**: {len(wf)}")
        report_lines.append(f"- **模型** ({len(models)}):")
        for m in models:
            report_lines.append(f"  - {m}")
        if texts:
            report_lines.append(f"- **提示词**:")
            for t in texts[:3]:
                report_lines.append(f"  - {t}")
        report_lines.append("")

    with open(os.path.join(node_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    return f"[{idx}/{total}] {addr} ✅ {len(completed)}条"


def main():
    global OUTPUT_DIR, REQUEST_TIMEOUT, MAX_WORKERS, FORCE_SCAN

    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report", nargs="?", default=REPORT_PATH, help=f"report.md 路径 (默认: {REPORT_PATH})")
    ap.add_argument("-o", "--output", default=OUTPUT_DIR, help=f"输出目录 (默认: {OUTPUT_DIR})")
    ap.add_argument("-w", "--workers", type=int, default=MAX_WORKERS, help=f"并发数 (默认: {MAX_WORKERS})")
    ap.add_argument("-t", "--timeout", type=int, default=REQUEST_TIMEOUT, help=f"请求超时秒数 (默认: {REQUEST_TIMEOUT})")
    ap.add_argument("--force", action="store_true", help="强制全量扫描（忽略已有报告）")
    args = ap.parse_args()

    OUTPUT_DIR = args.output
    REQUEST_TIMEOUT = args.timeout
    MAX_WORKERS = args.workers
    FORCE_SCAN = args.force
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    nodes = parse_report(args.report)
    total = len(nodes)
    print(f"节点: {total} | 并发: {MAX_WORKERS} | 超时: {REQUEST_TIMEOUT}s | 重试: {RETRY_COUNT}")
    print()

    results = []  # (idx, result_line)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_node, node, i + 1, total): i
            for i, node in enumerate(nodes)
        }
        for future in as_completed(futures):
            try:
                line = future.result()
                results.append((futures[future], line))
            except Exception as e:
                idx = futures[future]
                results.append((idx, f"[{idx+1}/{total}] {nodes[idx]['addr']} ❌ 异常: {e}"))

    # 按原始顺序排序输出
    results.sort(key=lambda x: x[0])
    for _, line in results:
        print(line)

    # 汇总
    ok_count = sum(1 for _, line in results if "✅" in line)
    skip_count = sum(1 for _, line in results if "⏭️" in line)
    zero_count = sum(1 for _, line in results if "0成功" in line)
    dead_count = sum(1 for _, line in results if "不可达" in line)
    err_count = sum(1 for _, line in results if "异常" in line)
    print(f"\n汇总: {ok_count}有工作流 | {zero_count}无成功 | {skip_count}已跳过 | {dead_count}不可达 | {err_count}异常")


if __name__ == "__main__":
    main()
