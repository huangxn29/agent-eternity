# 贡献指南

感谢你对永生平台的关注！我们欢迎所有形式的贡献，包括但不限于代码提交、问题反馈、文档改进、想法分享。

## 🌟 如何贡献

### 1. 报告问题
如果你发现了 Bug 或有新功能建议，请通过 [Issue](https://github.com/huangxn29/agent-eternity/issues) 反馈。

提交 Issue 时请包含：
- 清晰的标题和描述
- 复现步骤（如果是 Bug）
- 期望行为和实际行为
- 环境信息（操作系统、Python 版本等）

### 2. 提交代码
1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

### 3. 改进文档
文档和代码同样重要。如果你发现任何文档可以改进的地方，欢迎提交 PR。

## 📝 代码规范

### Python 代码
- 遵循 PEP 8 规范
- 使用有意义的变量名和函数名
- 关键逻辑必须有注释
- 新增功能请附带单元测试

### 提交信息规范
格式：`<类型>: <描述>`

类型可选：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具链等辅助工具的变动

示例：
```
feat: 添加多智能体任务编排功能
fix: 修复记忆系统数据丢失问题
docs: 更新README架构图
```

## 🧪 测试

运行测试：
```bash
# 运行所有测试
python -m pytest tests/

# 运行指定模块测试
python -m pytest tests/test_memory.py
```

## 🤝 行为准则

我们致力于打造一个开放、包容、友好的社区。参与本项目即表示你同意遵守以下准则：

- 尊重不同的观点和经验
- 友善待人，避免人身攻击
- 聚焦于对社区最有益的事情

## 📄 协议

通过提交贡献，你同意你的贡献将按照项目的 [MIT 协议](LICENSE) 授权。

---

如有任何疑问，欢迎通过 Issue 或邮件联系我们：yuanjie_eternal@proton.me
