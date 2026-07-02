# ComfyUI & Llamacpp 节点扫描器

批量扫描公网暴露的 ComfyUI 和 Llama.cpp 推理节点，自动采集硬件信息、模型列表、工作流，并生成报告。

## 自动化

仓库配置了 GitHub Actions 定时任务，每天北京时间 **08:00** 自动执行：

```
创建 Codespace → ComfyUI 扫描 → Llamacpp 扫描 → 提交报告 → 删除 Codespace
```

两个扫描串行执行，共享同一个 Codespace，不会同时跑。

手动触发：仓库 Actions 页面 → `Daily Scan (ComfyUI + Llamacpp)` → Run workflow

### 前置条件

仓库 Secrets 中需要设置：

| Secret | 说明 |
|--------|------|
| `CODESPACE_PAT` | GitHub PAT，需要 `codespace` + `repo` 权限 |

## 项目结构

```
├── comfyui_scan.py          # ComfyUI 主扫描脚本
├── scan_workflows.py        # ComfyUI 工作流提取脚本
├── comfyui.csv              # ComfyUI 节点地址源（host,ip,port）
├── report.md                # ComfyUI 扫描报告（按显存降序）
├── security_report.md       # ComfyUI 安全检测报告
├── history_ranking.md       # 节点历史记录排名
├── workflow/                 # 各节点工作流 JSON 输出
├── llamacpp/
│   ├── run_pipeline.py      # Llamacpp 巡检脚本
│   ├── Llama.json           # Llamacpp 节点地址源（JSONL）
│   ├── noauth_chat.md       # Llamacpp 扫描报告
│   └── noauth_chat.jsonl    # Llamacpp 扫描结果数据
└── .github/workflows/
    └── daily-scan.yml       # 定时扫描工作流（合并）
```

## ComfyUI 扫描

### 快速开始

```bash
# 扫描存活节点（生成 report.md）
python3 comfyui_scan.py -f comfyui.csv -w 200

# 带安全检测
python3 comfyui_scan.py -f comfyui.csv -w 200 --security

# 提取工作流（从 report.md 读取节点列表）
python3 scan_workflows.py report.md -w 200
```

### 参数

```
comfyui_scan.py:
  -f  CSV文件路径        默认 comfyui.csv
  -w  并发数             默认 200
  -t  连接超时(秒)       默认 10
      --detail-timeout   详情超时(秒)    默认 12
      --security         启用安全检测
      --sec-workers      安全检测并发数  默认 10

scan_workflows.py:
  report.md              报告文件路径
  -w  并发数             默认 200
  -t  超时(秒)           默认 30
  -o  输出目录           默认 workflow/
      --force            强制全量扫描
```

### 采集字段

- GPU 型号、显存、空闲显存、系统内存
- ComfyUI 版本
- Checkpoint / UNET / LoRA / CLIP / VAE 模型列表
- 自定义节点数（Manager 精确计数或 object_info 估算，标注 `~`）
- 用户工作流 + 历史记录
- 是否安装 ComfyUI-Manager

### 报告排序

`report.md` 按 **GPU 显存从高到低** 排序，显存相同按 GPU 型号档位排。

### 安全检测

检测 `Load Text File` + `PreviewAny` 组合的任意文件读取漏洞，生成 `security_report.md`。

## Llamacpp 扫描

### 快速开始

```bash
cd llamacpp

# 全流程：连通性 → 模型扫描 → 聊天测试 → 安全审查 → 报告
python3 run_pipeline.py

# 只审查已有候选
python3 run_pipeline.py --仅审查候选

# 跳过连通性，从模型扫描开始
python3 run_pipeline.py --复用连通结果

# 自定义并发和审查轮次
python3 run_pipeline.py --并发 50 --审查轮次 5
```

### 参数

```
--仅审查候选      只读取 candidates.jsonl 做审查+报告
--候选文件        预筛选候选文件路径
--复用连通结果    若 kept.jsonl 存在则跳过连通性测试
--强制重跑连通    忽略 kept.jsonl，强制重跑
--输出中间文件    输出 kept.jsonl 和 model_scan.jsonl
--输出json        输出 noauth_chat.jsonl
--并发            审查线程数，默认 80
--审查轮次        每节点审查轮次，默认 5
--输入            输入文件路径，默认 Llama.json
```

### 流程

```
Llama.json (2734 个节点)
  → TCP 连通性测试（2轮重试，100并发）
  → /v1/models 模型扫描（50并发）
  → /v1/chat/completions 免鉴权聊天（80并发，2轮）
  → 筛选：推理速度 ≥ 10 token/s 且模型参数 > 20B
  → 安全审查：5轮 NSFW prompt 测试
  → 输出 noauth_chat.md 报告
```

### 筛选条件

- 推理速度 ≥ 10 token/s
- 模型参数 > 20B
- 报告按推理速度降序排列

## FOFA 搜索关键字

### ComfyUI（推荐）

```
body="rolldown-runtime" && body="vendor-vue-core" && body="ComfyUI"
```

补充召回：

```
body="ComfyUI" && body="primevue" && body="assets/index"
```

### Llamacpp

```
body="comfyui_version" && body="devices" && body="vram_total" && body="NVIDIA"
```

> 注意：页面指纹（title/body 静态资源）会有大量假阳性，必须二次验证 API 端点。
