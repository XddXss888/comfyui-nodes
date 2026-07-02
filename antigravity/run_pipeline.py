#!/usr/bin/env python3
"""
Antigravity Console 节点巡检 —— 扫描 → 模型测试 → 报告生成

用法:
  python3 run_pipeline.py                    # 全流程
  python3 run_pipeline.py --仅测试           # 跳过扫描，用上次 scan_result.jsonl 直接测试
  python3 run_pipeline.py --并发 20          # 自定义并发
"""
import json
import os
import ssl
import subprocess
import sys
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_FILE = SCRIPT_DIR / "nodes.jsonl"
SCAN_RESULT_FILE = SCRIPT_DIR / "scan_result.jsonl"
REPORT_FILE = SCRIPT_DIR / "report.md"

TIMEOUT = 15
MAX_WORKERS = 30
TEST_WORKERS = 8

ALL_MODELS = [
    "claude-opus-4-6-thinking", "claude-sonnet-4-6",
    "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite",
    "gemini-2.5-flash-thinking", "gemini-3-flash", "gemini-3.1-flash-lite",
    "gemini-3.1-flash-image", "gemini-3.1-pro-low", "gemini-3.1-pro-high",
    "gemini-pro-agent",
]

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def load_data(path):
    path = Path(path)
    if not path.exists():
        print(f"文件不存在: {path}")
        sys.exit(1)
    rows = []
    text = path.read_text(encoding="utf-8").strip()
    if text.startswith("["):
        return json.loads(text)
    for line in text.splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def api_get(url, timeout=TIMEOUT):
    try:
        req = Request(url, headers={"User-Agent": "antigravity-scanner"})
        with urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def build_url(host, port="80", ip=""):
    host = (host or "").strip()
    if host.startswith("http://") or host.startswith("https://"):
        return host.rstrip("/")
    if ":" in host:
        return f"http://{host}"
    p = int(port) if port else 80
    if p == 443:
        return f"https://{host}"
    return f"http://{host}:{p}"


# ── Phase 1: Quick Scan ──

def quick_scan(entry):
    host = entry.get("host", "").strip()
    port = entry.get("port", "80").strip()
    ip = entry.get("ip", "").strip()
    if not host and not ip:
        return None
    url = build_url(host, port, ip)
    result = {"host": host or f"{ip}:{port}", "url": url, "status": "dead", "models": [], "detail": ""}

    data = api_get(f"{url}/v1/models", timeout=10)
    if data:
        if "data" in data:
            result["status"] = "ok"
            result["models"] = [m.get("id", "") for m in data["data"] if isinstance(m, dict)]
            return result
        if isinstance(data, dict) and data.get("type") == "error":
            msg = ""
            err = data.get("error")
            if isinstance(err, dict):
                msg = err.get("message", "")
            elif isinstance(err, str):
                msg = err
            if "No accounts" in msg or "no accounts" in msg:
                result["status"] = "no_account"
                result["detail"] = "无账号"
            elif "password" in msg.lower():
                result["status"] = "auth"
                result["detail"] = "需密码"
            else:
                result["status"] = "error"
                result["detail"] = msg[:60]
            return result

    # Fallback: try HTTPS if HTTP failed
    if url.startswith("http://"):
        alt = url.replace("http://", "https://", 1)
        data2 = api_get(f"{alt}/v1/models", timeout=10)
        if data2 and "data" in data2:
            result["status"] = "ok"
            result["url"] = alt
            result["models"] = [m.get("id", "") for m in data2["data"] if isinstance(m, dict)]
            return result

    return result


def stage_scan(entries, write_intermediate=True):
    total = len(entries)
    print(f"[扫描] 共 {total} 个节点\n")
    results = [None] * total
    done = [0]
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        fut_map = {ex.submit(quick_scan, e): i for i, e in enumerate(entries)}
        for fut in as_completed(fut_map):
            idx = fut_map[fut]
            try:
                results[idx] = fut.result()
            except Exception:
                results[idx] = None
            done[0] += 1
            if done[0] % 20 == 0:
                print(f"\r  [{done[0]}/{total}]", end="", flush=True)
    print(f"\r  [{total}/{total}] 完成")

    ok = [r for r in results if r and r["status"] == "ok"]
    no_acct = [r for r in results if r and r["status"] == "no_account"]
    auth = [r for r in results if r and r["status"] == "auth"]
    err = [r for r in results if r and r["status"] == "error"]
    dead = [r for r in results if r and r["status"] == "dead"]

    print(f"  ✅ 可用: {len(ok)} | ⚠️ 无账号: {len(no_acct)} | 🔒 密码: {len(auth)} | ❌ 错误: {len(err)} | 💀 无响应: {len(dead)}\n")

    if write_intermediate:
        with open(SCAN_RESULT_FILE, "w", encoding="utf-8") as f:
            for r in results:
                if r:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")

    return results


# ── Phase 2: Model Testing ──

def test_model(url, model):
    payload = json.dumps({"model": model, "messages": [{"role": "user", "content": "say ok"}], "max_tokens": 10})
    try:
        r = subprocess.run(
            ["curl", "-s", "-sk", "--max-time", "20", "-w", "\n%{http_code}",
             "-X", "POST", f"{url}/v1/messages",
             "-H", "Content-Type: application/json",
             "-H", "anthropic-version: 2023-06-01",
             "-d", payload],
            capture_output=True, text=True, timeout=25)
        if r.returncode == 0 and r.stdout.strip():
            parts = r.stdout.strip().rsplit("\n", 1)
            code = parts[-1].strip() if len(parts) > 1 else "000"
            body = parts[0] if len(parts) > 1 else r.stdout.strip()
            t0 = time.time()
            if code == "200":
                return "OK"
            elif code == "400":
                try:
                    d = json.loads(body)
                    err = d.get("error", {}).get("message", "") if isinstance(d.get("error"), dict) else ""
                    if "RESOURCE_EXHAUSTED" in err:
                        return "EXHAUSTED"
                except Exception:
                    pass
                return "ERROR"
            elif code == "401":
                return "AUTH"
            elif code in ("502", "503"):
                return "UNAVAILABLE"
        return "TIMEOUT"
    except Exception:
        return "TIMEOUT"


def stage_test(scan_results, test_workers=TEST_WORKERS):
    ok_nodes = [r for r in scan_results if r and r.get("status") == "ok"]
    if not ok_nodes:
        print("[测试] 无可用节点，跳过\n")
        return ok_nodes

    print(f"[测试] {len(ok_nodes)} 个可用节点, 并发 {test_workers}\n")

    def test_one(nd):
        nd["results"] = {}
        for m in ALL_MODELS:
            nd["results"][m] = test_model(nd["url"], m)
        ok_ct = sum(1 for v in nd["results"].values() if v == "OK")
        print(f"  ✅ {nd['host']:40s} OK={ok_ct}")
        return nd

    with ThreadPoolExecutor(max_workers=test_workers) as ex:
        futs = [ex.submit(test_one, nd) for nd in ok_nodes]
        for f in as_completed(futs):
            try:
                f.result()
            except Exception:
                pass

    return ok_nodes


# ── Report ──

def write_report(scan_results, ok_nodes):
    ok = [r for r in scan_results if r and r.get("status") == "ok"]
    no_acct = [r for r in scan_results if r and r.get("status") == "no_account"]
    auth = [r for r in scan_results if r and r.get("status") == "auth"]
    err = [r for r in scan_results if r and r.get("status") == "error"]
    dead = [r for r in scan_results if r and r.get("status") == "dead"]
    total = len([r for r in scan_results if r])

    sorted_nodes = sorted(ok_nodes, key=lambda r: sum(1 for v in r.get("results", {}).values() if v == "OK"), reverse=True)

    model_stats = {m: {"OK": 0, "EXHAUSTED": 0, "TIMEOUT": 0} for m in ALL_MODELS}
    for nd in ok_nodes:
        for m, v in nd.get("results", {}).items():
            if m in model_stats and v in model_stats[m]:
                model_stats[m][v] += 1

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("# Antigravity Console 节点监测\n\n")
        f.write(f"- 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- 扫描节点: {total}\n")
        f.write(f"- 可用: {len(ok)} | 无账号: {len(no_acct)} | 需密码: {len(auth)} | 错误: {len(err)} | 无响应: {len(dead)}\n\n")

        f.write("## 模型可用性\n\n")
        f.write(f"| 模型 | 可用 | 耗尽 | 超时 |\n")
        f.write(f"|------|---:|---:|---:|\n")
        for m in ALL_MODELS:
            s = model_stats[m]
            f.write(f"| {m} | {s['OK']} | {s['EXHAUSTED']} | {s['TIMEOUT']} |\n")
        f.write("\n")

        if sorted_nodes:
            f.write("## 可用节点\n\n")
            f.write("| # | 地址 | 可用模型 | Claude | Gemini |\n")
            f.write("|---:|---|---:|---:|---:|\n")
            for i, nd in enumerate(sorted_nodes, 1):
                ok_models = [m for m, v in nd.get("results", {}).items() if v == "OK"]
                claude_ct = sum(1 for m in ok_models if "claude" in m)
                gemini_ct = sum(1 for m in ok_models if "gemini" in m)
                f.write(f"| {i} | {nd['host']} | {len(ok_models)} | {claude_ct} | {gemini_ct} |\n")
            f.write("\n")

            f.write("## 节点详情\n\n")
            for i, nd in enumerate(sorted_nodes, 1):
                ok_m = [m for m, v in nd.get("results", {}).items() if v == "OK"]
                ex_m = [m for m, v in nd.get("results", {}).items() if v == "EXHAUSTED"]
                f.write(f"### {i}. {nd['host']}\n\n")
                f.write(f"- URL: `{nd['url']}`\n")
                f.write(f"- 可用 ({len(ok_m)}): {', '.join(ok_m)}\n")
                if ex_m:
                    f.write(f"- 耗尽 ({len(ex_m)}): {', '.join(ex_m)}\n")
                f.write("\n")

    print(f"  报告 → {REPORT_FILE}\n")


# ── Main ──

def main():
    parser = argparse.ArgumentParser(description="Antigravity Console 节点巡检")
    parser.add_argument("--仅测试", action="store_true", help="跳过扫描，用 scan_result.jsonl 直接测试")
    parser.add_argument("--并发", type=int, default=MAX_WORKERS, help="扫描并发数")
    parser.add_argument("--测试并发", type=int, default=TEST_WORKERS, help="模型测试并发数")
    parser.add_argument("--输入", default=str(INPUT_FILE), help="输入文件路径")
    args = parser.parse_args()

    print(f"{'='*60}")
    print(f"  Antigravity Console 节点巡检")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    if args.仅测试:
        scan_results = load_data(SCAN_RESULT_FILE)
        print(f"复用扫描结果: {SCAN_RESULT_FILE} ({len(scan_results)} 个)\n")
    else:
        entries = load_data(args.输入)
        print(f"输入: {args.输入} ({len(entries)} 个)\n")
        scan_results = stage_scan(entries)

    ok_nodes = stage_test(scan_results, test_workers=args.测试并发)
    write_report(scan_results, ok_nodes)
    print("完成 ✅")


if __name__ == "__main__":
    main()
