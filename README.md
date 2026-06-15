# ComfyUI Nodes Scanner

批量扫描公网 ComfyUI 节点，收集系统信息、GPU、模型、工作流等数据。

## 快速开始

```bash
# 1. 扫描存活节点（生成 report.md）
python3 comfyui_scan.py -f comfyui.csv -w 200

# 2. 提取工作流（从 report.md 读取节点列表）
python3 scan_workflows.py report.md -w 200
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `comfyui_scan.py` | 主扫描脚本，测活 + 采集详情 |
| `scan_workflows.py` | 工作流提取脚本，从历史记录导出 JSON |
| `comfyui.csv` | 服务器地址源文件 |
| `report.md` | 扫描结果总报告 |
| `workflow/` | 各节点工作流输出目录 |

## 扫描参数

### comfyui_scan.py

```
-f  CSV文件路径      默认 comfyui.csv
-w  并发数           默认 200
-t  连接超时(秒)     默认 10
    --detail-timeout  详情超时(秒)  默认 12
```

### scan_workflows.py

```
report.md           报告文件路径
-w  并发数           默认 200
-t  超时(秒)         默认 30
-o  输出目录         默认 workflow/
    --force          强制全量扫描（忽略已有报告）
```

## 采集字段

每个存活节点采集以下信息：

- **硬件**: GPU型号、显存、系统内存
- **软件**: ComfyUI版本
- **模型**: Checkpoint / UNET / LoRA / CLIP / VAE
- **自定义节点**: Manager管理的精确计数，无Manager时从object_info估算（标注`~`）
- **工作流**: 用户保存的工作流 + 历史记录中成功执行的流程
- **管理面板**: 是否安装 ComfyUI-Manager

## 输出格式

`report.md` 总览表 + 各节点详情：

```
| # | 地址 | 版本 | GPU | 显存 | 空闲 | 历史 | 管理 | 节点 | 工作流 | 模型数 | LoRA数 |
```

`workflow/{节点名}/` 目录下：

- `report.md` — 节点工作流报告
- `workflow_01.json` ~ `workflow_10.json` — 最近10个成功工作流
