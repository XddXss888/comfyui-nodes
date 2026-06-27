# 136.228.141.108:8188

**GPU**: RTX 5080 | **显存**: 15 GB | **空闲**: 12 GB
**内存**: 125 GB (空闲 99 GB)
**版本**: 0.26.0
**ComfyUI报告历史**: 有
**扫描时间**: 2026-06-27 08:08:06
**历史总数**: 6 | **成功**: 4

## 工作流列表

### 1. workflow_01.json
- **Prompt ID**: `90d80246-3477-4872-87ee-83013bf60c77`
- **类型**: 视频编辑
- **节点数**: 35
- **模型** (2):
  - gemma_3_12B_it_fp4_mixed.safetensors
  - ltx-2.3-22b-distilled-fp8.safetensors
- **提示词**:
  - [CLIPTextEncode::text] blurry, out of focus, overexposed, underexposed, low contrast, washed out colors, excessive noise, grainy texture, poor lighting, flickering, motion blur, distorted proportions, unnatural skin tones, 
  - [CLIPTextEncode::text] 固定镜头。背景是静帧保持不变。只是前面的人物@在讲话，保持色调风格不变，保持人物的一致性。

### 2. workflow_02.json
- **Prompt ID**: `0cf4a7b8-3317-4919-9bc6-889d8e4890d9`
- **类型**: 文生视频
- **节点数**: 13
- **模型** (4):
  - gummycandy_qwen.safetensors
  - qwen_2.5_vl_7b_fp8_scaled.safetensors
  - qwen_image_fp8_e4m3fn.safetensors
  - qwen_image_vae.safetensors

### 3. workflow_03.json
- **Prompt ID**: `451933ab-8889-422f-85a9-8e3b7acdb51d`
- **类型**: 文生视频
- **节点数**: 3
- **模型** (0):

### 4. workflow_04.json
- **Prompt ID**: `968e0496-ae6d-4118-a853-d26ec3364e57`
- **类型**: 文生视频
- **节点数**: 3
- **模型** (0):
