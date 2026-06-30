# 182.18.83.37:8188

**GPU**: RTX 5090 | **显存**: 31 GB | **空闲**: 31 GB
**内存**: 1 TB (空闲 1 TB)
**版本**: 0.20.1
**ComfyUI报告历史**: 有
**扫描时间**: 2026-06-30 08:06:47
**历史总数**: 24 | **成功**: 2

## 工作流列表

### 1. workflow_01.json
- **Prompt ID**: `918b70ee-14d0-4fe3-a32a-385aef1b31b5`
- **类型**: 文生图
- **节点数**: 13
- **模型** (4):
  - ae.safetensors
  - clip_l.safetensors
  - flux1-dev.safetensors
  - t5xxl_fp8_e4m3fn.safetensors
- **提示词**:
  - [CLIPTextEncode::text] low quality, blurry, distorted, ugly, watermark, text, logo, nsfw, realistic photo, 3d render

### 2. workflow_02.json
- **Prompt ID**: `07e6cb1a-4745-487e-bd95-7865a55a269d`
- **类型**: 图生视频
- **节点数**: 10
- **模型** (3):
  - umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - wan2.2_ti2v_5B_fp16.safetensors
  - wan2.2_vae.safetensors
- **提示词**:
  - [CLIPTextEncode::text] the woman slowly turns her head, hair flows in the wind, rain falls and splashes, subtle breathing, cinematic dynamic motion
  - [CLIPTextEncode::text] static, blurry, low quality, distorted, deformed, ugly, watermark, text
