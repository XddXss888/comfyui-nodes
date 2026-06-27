# 120.240.155.198:8123

**GPU**: A100 | **显存**: 39 GB | **空闲**: 16 GB
**内存**: 1007 GB (空闲 780 GB)
**版本**: 0.20.1
**ComfyUI报告历史**: 有
**扫描时间**: 2026-06-27 08:08:14
**历史总数**: 142 | **成功**: 10

## 工作流列表

### 1. workflow_01.json
- **Prompt ID**: `fd5e0f5b-f0e8-460d-9c35-e93bebc1addb`
- **类型**: 图生图
- **节点数**: 381
- **模型** (6):
  - Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors
  - dw-ll_ucoco_384_bs5.torchscript.pt
  - qe2511_consis_alpha_patched.safetensors
  - qwen_2.5_vl_7b_fp8_scaled.safetensors
  - qwen_image_edit_2511_fp8mixed.safetensors
  - qwen_image_vae.safetensors
- **提示词**:
  - [Text Multiline::text] 图1是衣服局部图，图2是胸针产品图。
将图2的胸针稳固地锚定在图1衣服的表面。
图像四周边缘区域的布料纹理、颜色、材质保持绝对不变，不作任何修改——这些边缘区域是未编辑的真实布料参照基准。
要求如下：
1. 胸针所有主体结构必须完全来自图2，禁止新增、删除或替换任何部件；
2. 衣服所有结构、纹理、颜色、褶皱和材质完全来自图1，严禁改变衣物本身的款式、版型或面料属性；
3. 胸针上柔性结构表现出真
  - [Text Multiline::text] 在胸针与衣料接触的位置生成真实、细腻、柔和的接触阴影和轻微环境遮蔽阴影
  - [TextEncodeQwenImageEditPlus::prompt] fake shadow, floating shadow, detached shadow, muddy shadow, dirty smudge, heavy dark patch, square shadow, halo edge, inconsistent lighting, inconsistent contact shadow, repainting artifacts, visible

### 2. workflow_02.json
- **Prompt ID**: `0affb6d7-4903-4848-a485-524c0dd61f54`
- **类型**: 其他
- **节点数**: 1
- **模型** (0):

### 3. workflow_03.json
- **Prompt ID**: `af8a856e-468c-4fd4-b1cc-be74a8a9c8c8`
- **类型**: 其他/工具
- **节点数**: 1
- **模型** (0):

### 4. workflow_04.json
- **Prompt ID**: `eab58c8e-6e9d-49f0-8487-d7eb8ccfd7ae`
- **类型**: 图生图
- **节点数**: 381
- **模型** (6):
  - Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors
  - dw-ll_ucoco_384_bs5.torchscript.pt
  - qe2511_consis_alpha_patched.safetensors
  - qwen_2.5_vl_7b_fp8_scaled.safetensors
  - qwen_image_edit_2511_fp8mixed.safetensors
  - qwen_image_vae.safetensors
- **提示词**:
  - [Text Multiline::text] 图1是衣服局部图，图2是胸针产品图。
将图2的胸针稳固地锚定在图1衣服的表面。
图像四周边缘区域的布料纹理、颜色、材质保持绝对不变，不作任何修改——这些边缘区域是未编辑的真实布料参照基准。
要求如下：
1. 胸针所有主体结构必须完全来自图2，禁止新增、删除或替换任何部件；
2. 衣服所有结构、纹理、颜色、褶皱和材质完全来自图1，严禁改变衣物本身的款式、版型或面料属性；
3. 胸针上柔性结构表现出真
  - [Text Multiline::text] 胸针完全融入均匀柔和的环境光照中，胸针主体的底部与衣物接触处，产生真实的、柔和的物理接触阴影；
  - [TextEncodeQwenImageEditPlus::prompt] fake shadow, floating shadow, detached shadow, muddy shadow, dirty smudge, heavy dark patch, square shadow, halo edge, inconsistent lighting, inconsistent contact shadow, repainting artifacts, visible

### 5. workflow_05.json
- **Prompt ID**: `2d2266cd-0475-44f1-90cc-22d5a0db2ad9`
- **类型**: 其他
- **节点数**: 1
- **模型** (0):

### 6. workflow_06.json
- **Prompt ID**: `6f16204e-a0e8-4658-9552-e9b3516766d5`
- **类型**: 其他/工具
- **节点数**: 1
- **模型** (0):

### 7. workflow_07.json
- **Prompt ID**: `8ce098a8-574a-4721-8549-668d5ca42821`
- **类型**: 图生图
- **节点数**: 381
- **模型** (6):
  - Qwen-Image-Edit-2511-Lightning-8steps-V1.0-bf16.safetensors
  - dw-ll_ucoco_384_bs5.torchscript.pt
  - qe2511_consis_alpha_patched.safetensors
  - qwen_2.5_vl_7b_fp8_scaled.safetensors
  - qwen_image_edit_2511_fp8mixed.safetensors
  - qwen_image_vae.safetensors
- **提示词**:
  - [Text Multiline::text] 图1是衣服局部图，图2是胸针产品图。
将图2的胸针稳固地锚定在图1衣服的表面。
图像四周边缘区域的布料纹理、颜色、材质保持绝对不变，不作任何修改——这些边缘区域是未编辑的真实布料参照基准。
要求如下：
1. 胸针所有主体结构必须完全来自图2，禁止新增、删除或替换任何部件；
2. 衣服所有结构、纹理、颜色、褶皱和材质完全来自图1，严禁改变衣物本身的款式、版型或面料属性；
3. 胸针上柔性结构表现出真
  - [Text Multiline::text] 胸针完全融入均匀柔和的环境光照中，胸针主体的底部与衣物接触处，产生真实的、柔和的物理接触阴影；
  - [TextEncodeQwenImageEditPlus::prompt] fake shadow, floating shadow, detached shadow, muddy shadow, dirty smudge, heavy dark patch, square shadow, halo edge, inconsistent lighting, inconsistent contact shadow, repainting artifacts, visible

### 8. workflow_08.json
- **Prompt ID**: `6c8eaadc-a575-4aed-b60a-fce2ee571ade`
- **类型**: 其他
- **节点数**: 1
- **模型** (0):

### 9. workflow_09.json
- **Prompt ID**: `23bb95c3-1926-48fb-9a05-3492cd8372af`
- **类型**: 其他/工具
- **节点数**: 1
- **模型** (0):

### 10. workflow_10.json
- **Prompt ID**: `7135ac9a-b9fa-4b0a-9997-1174bf4709bb`
- **类型**: 其他
- **节点数**: 1
- **模型** (0):
