# 116.228.88.61:4000

**GPU**: A40 | **显存**: 44 GB | **空闲**: 13 GB
**内存**: 125 GB (空闲 108 GB)
**版本**: 0.19.1
**ComfyUI报告历史**: 有
**扫描时间**: 2026-06-14 05:56:14
**历史总数**: 2 | **成功**: 2

## 工作流列表

### 1. workflow_01.json
- **Prompt ID**: `8d849ee1-0367-4361-8325-14d1c5cf0fbc`
- **类型**: 文生视频
- **节点数**: 3
- **模型** (0):

### 2. workflow_02.json
- **Prompt ID**: `1853c2dc-d3a0-4767-88d3-abd60e06e16d`
- **类型**: 视频超分/处理
- **节点数**: 45
- **模型** (5):
  - gemma_3_12B_it_fp8_e4m3fn.safetensors
  - ltx-2.3-22b-dev-fp8.safetensors
  - ltx-2.3-22b-dev.safetensors
  - ltx-2.3-22b-distilled-lora-384.safetensors
  - ltx-2.3-spatial-upscaler-x2-1.1.safetensors
- **提示词**:
  - [CLIPTextEncode::text] pc game, console game, video game, cartoon, childish, ugly
