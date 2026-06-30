# 82.67.123.150:8188

**GPU**: RTX 4060 Ti | **显存**: 8 GB | **空闲**: 6 GB
**内存**: 53 GB (空闲 9 GB)
**版本**: 0.26.0
**ComfyUI报告历史**: 有
**扫描时间**: 2026-06-30 08:06:49
**历史总数**: 3 | **成功**: 3

## 工作流列表

### 1. workflow_01.json
- **Prompt ID**: `dbba770d-a6d2-41ee-a92e-397d93fdde82`
- **类型**: 文生图
- **节点数**: 18
- **模型** (3):
  - flux-2-klein-base-9b-fp8.safetensors
  - flux2-vae.safetensors
  - qwen_3_8b_fp8mixed.safetensors

### 2. workflow_02.json
- **Prompt ID**: `108540b2-d7e7-4d77-9d00-e5e234eff5d7`
- **类型**: 文生图
- **节点数**: 16
- **模型** (3):
  - flux-2-klein-base-9b-fp8.safetensors
  - flux2-vae.safetensors
  - qwen_3_8b_fp8mixed.safetensors

### 3. workflow_03.json
- **Prompt ID**: `659dbfc4-84ef-4076-bb83-a9a602a8cc0c`
- **类型**: 图生视频
- **节点数**: 32
- **模型** (6):
  - umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors
  - wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors
  - wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors
  - wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors
  - wan_2.1_vae.safetensors
- **提示词**:
  - [CLIPTextEncode::text] 色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走
  - [CLIPTextEncode::text] Wide cinematic shot of a massive, intricate steampunk zeppelin soaring majestically through a dramatic sky at sunset. The airship features highly detailed copper plating, exposed brass gears turning s
