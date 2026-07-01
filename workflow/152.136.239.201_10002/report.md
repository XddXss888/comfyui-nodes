# 152.136.239.201:10002

**GPU**: H20 | **显存**: 95 GB | **空闲**: 48 GB
**内存**: 618 GB (空闲 557 GB)
**版本**: 0.19.3
**ComfyUI报告历史**: 有
**扫描时间**: 2026-07-01 08:08:25
**历史总数**: 16 | **成功**: 3

## 工作流列表

### 1. workflow_01.json
- **Prompt ID**: `0068ab9e-a153-42af-b285-cc7db251d4ca`
- **类型**: 文生图
- **节点数**: 15
- **模型** (5):
  - Wan/lightx2v_T2V_14B_cfg_step_distill_v2_lora_rank64_bf16_.safetensors
  - umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - wan2.2/Wan2_2-T2V-A14B-LOW_fp8_e4m3fn_scaled_KJ.safetensors
  - wan2.2/Wan2_2-T2V-A14B_HIGH_fp8_e4m3fn_scaled_KJ.safetensors
  - wan_2.1_vae.safetensors

### 2. workflow_02.json
- **Prompt ID**: `eac0b259-6efe-470f-840d-28cbe3abcc03`
- **类型**: 文生图
- **节点数**: 15
- **模型** (5):
  - Wan/lightx2v_T2V_14B_cfg_step_distill_v2_lora_rank64_bf16_.safetensors
  - umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - wan2.2/Wan2_2-T2V-A14B-LOW_fp8_e4m3fn_scaled_KJ.safetensors
  - wan2.2/Wan2_2-T2V-A14B_HIGH_fp8_e4m3fn_scaled_KJ.safetensors
  - wan_2.1_vae.safetensors
- **提示词**:
  - [CLIPTextEncode::text] 一个50岁的中国人能和15岁的中国女人在亲吻
  - [CLIPTextEncode::text] 一个中国男人和一个日本女人。

### 3. workflow_03.json
- **Prompt ID**: `8e0e5682-898b-4685-9475-b9238b6f662d`
- **类型**: 图生图
- **节点数**: 13
- **模型** (4):
  - Qwen-Image/Qwen-Image-Edit-Lightning-8steps-V1.0-bf16.safetensors
  - Qwen-Image/qwen_image_edit_2511_bf16.safetensors
  - qwen_2.5_vl_7b_fp8_scaled.safetensors
  - qwen_image_vae.safetensors
- **提示词**:
  - [TextEncodeQwenImageEditPlus::prompt] remove microphone from hand, change to full body wide shot showing complete body, keep everything else unchanged, same person, same clothing, same scene, same lighting
