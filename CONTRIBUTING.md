# 贡献指南

感谢您对 UnveilChem 项目的关注！我们欢迎所有形式的贡献。

## 🤝 如何贡献

### 报告问题

如果您发现了 bug 或有功能建议，请：

1. 检查 [Issues](https://github.com/Stanljinjin54/UnveilChem_AiFiller/issues) 确认问题未被报告
2. 创建新的 Issue，使用合适的模板
3. 提供详细的问题描述和复现步骤

### 提交代码

#### 1. Fork 仓库

点击 GitHub 页面右上角的 "Fork" 按钮

#### 2. 克隆仓库

```bash
git clone https://github.com/Stanljinjin54/UnveilChem_AiFiller.git
cd UnveilChem
```

#### 3. 创建分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

#### 4. 进行开发

- 遵循项目的代码风格
- 添加必要的测试
- 更新相关文档

#### 5. 提交更改

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```bash
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug in parser"
git commit -m "docs: update README"
git commit -m "style: format code"
git commit -m "refactor: improve code structure"
git commit -m "test: add unit tests"
git commit -m "chore: update dependencies"
```

#### 6. 推送到远程

```bash
git push origin feature/your-feature-name
```

#### 7. 创建 Pull Request

- 访问您的 Fork 仓库
- 点击 "New Pull Request"
- 填写 PR 模板
- 等待代码审查

## 📋 开发规范

### 代码风格

#### Python (后端)

- 遵循 PEP 8 规范
- 使用 4 空格缩进
- 最大行长度 120 字符
- 添加类型注解
- 编写 docstring

```python
def parse_document(file_path: str) -> Dict[str, Any]:
    """
    解析文档文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        解析结果字典
    """
    pass
```

#### TypeScript (前端)

- 使用 ESLint 和 Prettier
- 使用 2 空格缩进
- 添加类型定义
- 使用函数式组件

```typescript
interface DocumentData {
  content: string;
  parameters: Record<string, any>;
}

const DocumentParser: React.FC<{ file: File }> = ({ file }) => {
  // ...
};
```

### 提交规范

使用 Conventional Commits 规范：

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具链相关

### 测试要求

- 新功能必须包含测试
- Bug 修复需要添加回归测试
- 保持测试覆盖率 > 80%

### 文档要求

- 新功能需要更新 README 或相关文档
- API 变更需要更新 API 文档
- 重大变更需要更新 CHANGELOG

## 🛠️ 开发环境

### 后端开发

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

### 代码检查

```bash
# 后端
cd backend
black .
flake8 .
mypy .

# 前端
cd frontend
npm run lint
npm run type-check
npm run format
```

## 📝 PR 模板

创建 Pull Request 时，请填写以下信息：

### 描述

简要描述此 PR 的目的和变更内容。

### 变更类型

- [ ] 新功能
- [ ] Bug 修复
- [ ] 文档更新
- [ ] 代码重构
- [ ] 性能优化
- [ ] 测试相关
- [ ] 其他

### 测试

- [ ] 已添加测试用例
- [ ] 所有测试通过
- [ ] 已进行手动测试

### 检查清单

- [ ] 代码遵循项目规范
- [ ] 已更新相关文档
- [ ] 已添加必要的注释
- [ ] 无 console.log 或调试代码
- [ ] 合并后无冲突

### 相关 Issue

关闭 #(issue number)

## 🎯 优先级

我们优先处理以下类型的贡献：

1. 🔴 高优先级
   - 安全漏洞修复
   - 严重 bug 修复
   - 核心功能增强

2. 🟡 中优先级
   - 新功能实现
   - 性能优化
   - 用户体验改进

3. 🟢 低优先级
   - 文档完善
   - 代码重构
   - 小功能改进

## 📧 联系方式

如有疑问，请通过以下方式联系：

- GitHub Issues: [提交问题](https://github.com/Stanljinjin54/UnveilChem_AiFiller/issues)
- Email: 549057226@qq.com

## 🙏 感谢

再次感谢您的贡献！您的每一个 PR 都让 UnveilChem 变得更好。
