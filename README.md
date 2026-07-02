# Public Nodes

公网 AI 推理节点自动化扫描与监测。每个子目录是一个独立项目，每天自动扫描并生成报告。

## 项目列表

| 目录 | 说明 | 报告 |
|------|------|------|
| `comfyui/` | ComfyUI 节点扫描（GPU/模型/工作流/安全） | `comfyui/report.md` |
| `llamacpp/` | Llama.cpp 推理节点巡检（免鉴权/速度/审查） | `llamacpp/noauth_chat.md` |
| `antigravity/` | Antigravity Console 扫描（Claude/Gemini 代理） | `antigravity/report.md` |

## 自动化

每天北京时间 **08:00** 自动执行（一个 Codespace 串行跑所有项目）：

```
创建 Codespace → comfyui 扫描 → llamacpp 扫描 → antigravity 扫描 → 提交报告 → 删除 Codespace
```

手动触发：Actions → `Daily Scan` → Run workflow

### 添加新项目

1. 创建新目录，放入扫描脚本和数据文件
2. 在 `.github/workflows/daily-scan.yml` 里复制一个 project block：

```yaml
      # ────────────────────────────────────────────
      # Project: 新项目名
      # ────────────────────────────────────────────
      - name: "新项目名: scan"
        run: |
          cs="${{ steps.codespace.outputs.name }}"
          gh codespace ssh -c "${cs}" -- \
            "cd ${WS}/新项目名 && python3 你的脚本.py"

      - name: "新项目名: copy reports"
        run: |
          cs="${{ steps.codespace.outputs.name }}"
          gh codespace cp -c "${cs}" -e "remote:${WS}/新项目名/报告文件" 新项目名/报告文件
```

3. 在 Commit 步骤的 `git add` 里加上新报告路径

### 前置条件

| Secret | 说明 |
|--------|------|
| `CODESPACE_PAT` | GitHub PAT，需要 `codespace` + `repo` 权限 |

## 仓库结构

```
├── README.md
├── .github/workflows/daily-scan.yml
├── comfyui/
│   ├── comfyui_scan.py        # 主扫描脚本
│   ├── scan_workflows.py      # 工作流提取
│   ├── comfyui.csv            # 节点地址源
│   ├── report.md              # 扫描报告（按显存降序）
│   ├── security_report.md     # 安全检测报告
│   └── workflow/              # 各节点工作流 JSON
├── llamacpp/
│   ├── run_pipeline.py        # 巡检脚本
│   ├── Llama.json             # 节点地址源
│   ├── noauth_chat.md         # 扫描报告
│   └── noauth_chat.jsonl      # 结果数据
└── antigravity/
    ├── run_pipeline.py        # 巡检脚本
    ├── nodes.jsonl            # 节点地址源
    └── report.md              # 扫描报告
```

---

## ComfyUI 扫描

```bash
cd comfyui
python3 comfyui_scan.py -f comfyui.csv -w 200
python3 comfyui_scan.py -f comfyui.csv -w 200 --security
python3 scan_workflows.py report.md -w 200
```

详细参数见 `comfyui_scan.py --help`。

报告按 GPU 显存从高到低排序。

## Llamacpp 扫描

```bash
cd llamacpp
python3 run_pipeline.py                    # 全流程
python3 run_pipeline.py --复用连通结果      # 跳过连通性
python3 run_pipeline.py --并发 50          # 自定义并发
```

流程：连通性 → 模型扫描 → 聊天测试 → 安全审查 → 报告

筛选条件：推理速度 ≥ 10 t/s 且模型参数 > 20B

## FOFA 搜索关键字

**ComfyUI：**
```
body="rolldown-runtime" && body="vendor-vue-core" && body="ComfyUI"
```

**Llamacpp：**
```
body="comfyui_version" && body="devices" && body="vram_total" && body="NVIDIA"
```

## Antigravity Console 扫描

```bash
cd antigravity
python3 run_pipeline.py                    # 全流程
python3 run_pipeline.py --仅测试           # 跳过扫描，用上次结果直接测试
python3 run_pipeline.py --并发 20          # 自定义并发
```

流程：节点扫描（/v1/models）→ 逐模型请求测试 → 报告

检测内容：
- Claude (opus-4-6-thinking, sonnet-4-6)
- Gemini (2.5-pro/flash, 3-flash, 3.1-pro/flash 等)
- 账户状态、配额、密码保护
