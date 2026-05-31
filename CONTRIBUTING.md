# 贡献指南

感谢你对本项目感兴趣！欢迎任何形式的贡献。

## 提交 Issue

- **Bug 报告**：请描述复现步骤、你的环境（GPU 型号、GPT-SoVITS 版本、操作系统），以及完整的错误输出。
- **功能建议**：描述你想要的功能和使用场景。

## 提交 Pull Request

1. Fork 本仓库
2. 创建分支：`git checkout -b feature/你的功能名`
3. 提交改动：`git commit -m "描述你的改动"`
4. 推送分支：`git push origin feature/你的功能名`
5. 创建 Pull Request

## 代码规范

- Python 代码遵循 PEP 8
- 保持 `galgame_voice.py` 的命令行接口兼容性
- 训练相关的 subprocess 调用**不要**使用 `capture_output=True`
- 添加必要的中文注释
