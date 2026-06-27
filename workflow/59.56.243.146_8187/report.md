# 59.56.243.146:8187

**GPU**: RTX 5090 | **显存**: 32 GB | **空闲**: 3 GB
**内存**: 63 GB (空闲 42 GB)
**版本**: 0.20.1
**ComfyUI报告历史**: 有
**扫描时间**: 2026-06-27 08:07:52
**历史总数**: 4 | **成功**: 4

## 工作流列表

### 1. workflow_01.json
- **Prompt ID**: `0254e26b-0a85-4209-b388-3fc491f6d3d0`
- **类型**: 图生图
- **节点数**: 15
- **模型** (5):
  - Qwen-Image-Edit-2509_fp8_e4m3fn.safetensors
  - qwen\2509\提取纹理extract_texture_qwen_image_edit_2509_V1.safetensors
  - qwen\qwen_2.5_vl_7b.safetensors
  - qwen\qwen_image_vae.safetensors
  - qwen\加速\Qwen-Image-Edit-Lightning-4steps-V1.0.safetensors
- **提示词**:
  - [TextEncodeQwenImageEditPlus::prompt] 从T恤中提取印花。提取为印花图像。背景参考衣服颜色来。印花满铺图，不要有衣物纹理。使图像高清化。

### 2. workflow_02.json
- **Prompt ID**: `11d898fd-1c25-4762-9138-abb9eff0b6d0`
- **类型**: 图生图
- **节点数**: 24
- **模型** (4):
  - F.1\diffusion_models\flux1-kontext-dev.safetensors
  - FLUX\ae.sft
  - clip_l.safetensors
  - t5xxl_fp8_e4m3fn.safetensors
- **提示词**:
  - [CLIPTextEncode::text] Identify the main subject in the image, convert it to pure white and the background to absolute black, while keeping the subject’s original position unchanged.

### 3. workflow_03.json
- **Prompt ID**: `6e6e0607-4d59-4d29-bcae-62b36ba0a8b1`
- **类型**: 图生图
- **节点数**: 15
- **模型** (5):
  - Qwen-Image-Edit-2509_fp8_e4m3fn.safetensors
  - qwen\2509\提取纹理extract_texture_qwen_image_edit_2509_V1.safetensors
  - qwen\qwen_2.5_vl_7b.safetensors
  - qwen\qwen_image_vae.safetensors
  - qwen\加速\Qwen-Image-Edit-Lightning-4steps-V1.0.safetensors
- **提示词**:
  - [TextEncodeQwenImageEditPlus::prompt] 从T恤中提取印花。提取为印花图像。背景参考衣服颜色来。印花满铺图，不要有衣物纹理。使图像高清化。

### 4. workflow_04.json
- **Prompt ID**: `59738fd8-3ba6-490e-bbe2-fe69ca400e8e`
- **类型**: 图生图
- **节点数**: 24
- **模型** (4):
  - F.1\diffusion_models\flux1-kontext-dev.safetensors
  - FLUX\ae.sft
  - clip_l.safetensors
  - t5xxl_fp8_e4m3fn.safetensors
- **提示词**:
  - [CLIPTextEncode::text] Identify the main subject in the image, convert it to pure white and the background to absolute black, while keeping the subject’s original position unchanged.
