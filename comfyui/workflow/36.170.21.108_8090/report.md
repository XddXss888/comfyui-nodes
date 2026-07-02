# 36.170.21.108:8090

**GPU**: RTX 4090 | **显存**: 24 GB | **空闲**: 15 GB
**内存**: 503 GB (空闲 464 GB)
**版本**: 0.18.1
**ComfyUI报告历史**: 有
**扫描时间**: 2026-06-13 23:54:50
**历史总数**: 9 | **成功**: 6

## 工作流列表

### 1. workflow_01.json
- **Prompt ID**: `bba2da97-86fd-4cb2-9625-664171989ce5`
- **类型**: 文生图
- **节点数**: 11
- **模型** (3):
  - Z_image/BEYOND REALITY SUPER Z IMAGE 3.0 淡妆浓抹 BF16.safetensors
  - ae.safetensors
  - qwen_3_4b.safetensors

### 2. workflow_02.json
- **Prompt ID**: `a5a878cb-25c2-4dd8-9a5e-9a8302378a8f`
- **类型**: 视频超分/处理
- **节点数**: 55
- **模型** (7):
  - LTX2_KJ/LTX23_video_vae_bf16.safetensors
  - LTX2_KJ/LTX2_audio_vae_bf16.safetensors
  - LTX2_KJ/ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors
  - LTX2_KJ/ltx-2.3_text_projection_bf16.safetensors
  - gemma/gemma-3-12b-it-abliterated_heretic_lora_rank64_bf16.safetensors
  - gemma/gemma_3_12B_it_fp8_e4m3fn.safetensors
  - ltx-2.3-spatial-upscaler-x2-1.0.safetensors
- **提示词**:
  - [CLIPTextEncode::text] pc game, console game, video game, cartoon, childish, ugly

### 3. workflow_03.json
- **Prompt ID**: `d6871700-d735-41e3-9955-6146ce4b5d4d`
- **类型**: 视频超分/处理
- **节点数**: 55
- **模型** (7):
  - LTX2_KJ/LTX23_video_vae_bf16.safetensors
  - LTX2_KJ/LTX2_audio_vae_bf16.safetensors
  - LTX2_KJ/ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors
  - LTX2_KJ/ltx-2.3_text_projection_bf16.safetensors
  - gemma/gemma-3-12b-it-abliterated_heretic_lora_rank64_bf16.safetensors
  - gemma/gemma_3_12B_it_fp8_e4m3fn.safetensors
  - ltx-2.3-spatial-upscaler-x2-1.0.safetensors
- **提示词**:
  - [CLIPTextEncode::text] pc game, console game, video game, cartoon, childish, ugly

### 4. workflow_04.json
- **Prompt ID**: `bcfe5ae3-101c-48eb-b1d8-2367521b31bc`
- **类型**: 图生图
- **节点数**: 31
- **模型** (3):
  - Flux2/flux-2-klein-9b-fp8.safetensors
  - Flux2/flux2-vae.safetensors
  - qwen/qwen_3_8b_fp8mixed.safetensors
- **提示词**:
  - [CLIPTextEncode::text] 让图1的美女截上图3的耳环，抱着戴着图2帽子的图4的猫。

### 5. workflow_05.json
- **Prompt ID**: `b08431fc-1d5b-423f-b324-08a786c5706e`
- **类型**: 图生图
- **节点数**: 31
- **模型** (3):
  - Flux2/flux-2-klein-9b-fp8.safetensors
  - Flux2/flux2-vae.safetensors
  - qwen/qwen_3_8b_fp8mixed.safetensors
- **提示词**:
  - [CLIPTextEncode::text] 让图1的美女截上图3的耳环，抱着戴着图2帽子的图4的猫。

### 6. workflow_06.json
- **Prompt ID**: `b8a117fa-fa0b-45ed-8b06-93012a83b5fb`
- **类型**: 文生图
- **节点数**: 20
- **模型** (4):
  - Flux2/flux-2-klein-9b.safetensors
  - Flux2/flux2-vae.safetensors
  - FluxKlein/Kook_Flux_klein_亚洲人像.safetensors
  - qwen/qwen_3_8b.safetensors
