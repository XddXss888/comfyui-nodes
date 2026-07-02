# https://virtucomfy.ddns.net

**GPU**: RTX PRO 6000 BB | **显存**: 95 GB | **空闲**: 83 GB
**内存**: 188 GB (空闲 105 GB)
**版本**: 0.25.0
**ComfyUI报告历史**: 有
**扫描时间**: 2026-07-02 08:09:43
**历史总数**: 61 | **成功**: 10

## 工作流列表

### 1. workflow_01.json
- **Prompt ID**: `b988f73c-8160-4b97-b7a9-d3f9e301134d`
- **类型**: 视频超分/处理
- **节点数**: 77
- **模型** (7):
  - LTX23_audio_vae_bf16.safetensors
  - LTX23_video_vae_bf16.safetensors
  - gemma_3_12B_it_fp8_scaled.safetensors
  - ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors
  - ltx-2.3-spatial-upscaler-x2-1.1.safetensors
  - ltx-2.3_text_projection_bf16.safetensors
  - taeltx2_3.safetensors
- **提示词**:
  - [CLIPTextEncode::text] scene cut, scene transition, no movement, blurry, low quality, still frame, frames, watermark, overlay, titles, subtitles
  - [CLIPTextEncode::text] music, score, instruments, songs, violin, strings, orchestra, symphony, symphonic, horn
  - [CLIPTextEncode::text] A static shot of a girl waving away at the boy. Do not add camera movement

### 2. workflow_02.json
- **Prompt ID**: `45b6460e-6914-451f-93cc-252abf836ef0`
- **类型**: 视频超分/处理
- **节点数**: 104
- **模型** (7):
  - LTX23_audio_vae_bf16.safetensors
  - LTX23_video_vae_bf16.safetensors
  - gemma_3_12B_it_fp8_scaled.safetensors
  - ltx-2.3-22b-distilled_transformer_only_fp8_input_scaled_v3.safetensors
  - ltx-2.3-spatial-upscaler-x2-1.1.safetensors
  - ltx-2.3_text_projection_bf16.safetensors
  - taeltx2_3.safetensors
- **提示词**:
  - [CLIPTextEncode::text] scene cut, scene transition, no movement, blurry, low quality, still frame, frames, watermark, overlay, titles, subtitles
  - [CLIPTextEncode::text] music, score, instruments, songs, violin, strings, orchestra, symphony, symphonic, horn
  - [CLIPTextEncode::text] A static shot of a girl waving away at the boy. Do not add camera movement

### 3. workflow_03.json
- **Prompt ID**: `6112d848-b44b-4f5a-b03b-65bf118600c4`
- **类型**: 图生视频
- **节点数**: 18
- **模型** (4):
  - umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - wan2.2/wan2.2_i2v_A14b_high_noise_lightx2v_4step-Q6_K.gguf
  - wan2.2/wan2.2_i2v_A14b_low_noise_lightx2v_4step-Q6_K.gguf
  - wan_2.1_vae.safetensors
- **提示词**:
  - [CLIPTextEncode::text] Anime key visual animation, 2D cel-shaded style. medium shot of the anime girl running desperately to the left. Intense and expressive panicked face with sweat drops flying off. Dust smoke clouds kick

### 4. workflow_04.json
- **Prompt ID**: `636e98d4-d77b-469a-aef0-84c78f8334ba`
- **类型**: 图生视频
- **节点数**: 18
- **模型** (4):
  - umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - wan2.2/wan2.2_i2v_A14b_high_noise_lightx2v_4step-Q6_K.gguf
  - wan2.2/wan2.2_i2v_A14b_low_noise_lightx2v_4step-Q6_K.gguf
  - wan_2.1_vae.safetensors
- **提示词**:
  - [CLIPTextEncode::text] Anime key visual animation, 2D cel-shaded style. medium shot of the anime girl running desperately to the left. Intense and expressive panicked face with sweat drops flying off. Dust smoke clouds kick

### 5. workflow_05.json
- **Prompt ID**: `1873ade0-8a58-4e50-85a7-3702f842ac20`
- **类型**: 图生视频
- **节点数**: 18
- **模型** (4):
  - umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - wan2.2/wan2.2_i2v_A14b_high_noise_lightx2v_4step-Q6_K.gguf
  - wan2.2/wan2.2_i2v_A14b_low_noise_lightx2v_4step-Q6_K.gguf
  - wan_2.1_vae.safetensors
- **提示词**:
  - [CLIPTextEncode::text] 2D anime style, high-quality Japanese animation, cel-shaded. Static camera, locked shot, no camera movement. The blue-haired anime schoolgirl from the reference image bumps into the black-haired anime

### 6. workflow_06.json
- **Prompt ID**: `d9e9efa9-689d-4820-96e0-7531a5d2d996`
- **类型**: 图生视频
- **节点数**: 20
- **模型** (4):
  - umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - wan2.2/wan2.2_i2v_A14b_high_noise_lightx2v_4step-Q6_K.gguf
  - wan2.2/wan2.2_i2v_A14b_low_noise_lightx2v_4step-Q6_K.gguf
  - wan_2.1_vae.safetensors
- **提示词**:
  - [CLIPTextEncode::text] 2D anime style, high-quality Japanese animation, cel-shaded. Static camera, locked shot, no camera movement. The black-haired anime boy with glasses from the reference image is eating breakfast at the

### 7. workflow_07.json
- **Prompt ID**: `2b5d3991-403d-48b3-9d60-77fc989b0a1f`
- **类型**: 图片超分
- **节点数**: 93
- **模型** (7):
  - 4x-UltraSharp.pth
  - 4x_NMKD-Superscale-SP_178000_G.pth
  - ViT-L-14-BEST-smooth-GmP-ft.safetensors
  - ae.safetensors
  - clip_g.safetensors
  - fluxSigmaVision_fp16.safetensors
  - t5xxl_fp8_e4m3fn.safetensors
- **提示词**:
  - [CLIPTextEncode::text] (cartoon:0.5)
  - [CLIPTextEncode::text] (cartoon:0.5)
  - [CLIPTextEncode::text] (cartoon:0.5)

### 8. workflow_08.json
- **Prompt ID**: `12e424e1-834a-4dff-8ad7-0cb62c00d123`
- **类型**: 图生视频
- **节点数**: 20
- **模型** (4):
  - umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - wan2.2/wan2.2_i2v_A14b_high_noise_lightx2v_4step-Q6_K.gguf
  - wan2.2/wan2.2_i2v_A14b_low_noise_lightx2v_4step-Q6_K.gguf
  - wan_2.1_vae.safetensors
- **提示词**:
  - [CLIPTextEncode::text] static shot of the girl shocked

### 9. workflow_09.json
- **Prompt ID**: `076e06e8-042d-4e86-84bb-17fd1a5c15b9`
- **类型**: 图片超分
- **节点数**: 93
- **模型** (7):
  - 4x_NMKD-Superscale-SP_178000_G.pth
  - 8x_NMKD-Superscale_150000_G.pth
  - ViT-L-14-BEST-smooth-GmP-ft.safetensors
  - ae.safetensors
  - clip_g.safetensors
  - fluxSigmaVision_fp16.safetensors
  - t5xxl_fp8_e4m3fn.safetensors
- **提示词**:
  - [CLIPTextEncode::text] (cartoon:0.5)
  - [CLIPTextEncode::text] (cartoon:0.5)
  - [CLIPTextEncode::text] (cartoon:0.5)

### 10. workflow_10.json
- **Prompt ID**: `f5e16cf4-c1b2-47b1-b883-7fcc34066729`
- **类型**: 图生视频
- **节点数**: 18
- **模型** (4):
  - umt5_xxl_fp8_e4m3fn_scaled.safetensors
  - wan2.2/wan2.2_i2v_A14b_high_noise_lightx2v_4step-Q6_K.gguf
  - wan2.2/wan2.2_i2v_A14b_low_noise_lightx2v_4step-Q6_K.gguf
  - wan_2.1_vae.safetensors
- **提示词**:
  - [CLIPTextEncode::text] 2D anime style, high-quality Japanese animation, cel-shaded. Static camera, locked shot, no camera movement. 

The boy found is surprised looking at below
