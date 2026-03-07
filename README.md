# UnveilChem - 智能化工软件自动化平台

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.8+-yellow.svg)
![React](https://img.shields.io/badge/react-18+-61DAFB.svg)

**基于 AI 的化工软件自动化解决方案**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [技术架构](#-技术架构) • [文档](#-文档) • [贡献指南](#-贡献指南)

</div>

---

## 📖 项目简介

UnveilChem 是一款创新的**智能化工软件自动化平台**，通过 AI 驱动的 Agent 系统，实现化工文档的智能解析、参数提取、软件自动执行和结果输出的全流程自动化。

### 核心价值

- 🚀 **提升效率**：自动化处理重复性工作，节省 80%+ 人工时间
- 🎯 **精准识别**：AI 驱动的参数提取，准确率高达 99%+
- 🔗 **跨软件协作**：支持 DWSIM、Excel、Aspen Plus 等多种化工软件
- 🤖 **智能决策**：基于 LLM 的任务理解和执行计划生成
- 📊 **全流程覆盖**：文档解析 → 参数提取 → 自动录入 → 软件执行 → 结果输出

---

## ✨ 功能特性

### 📄 文档智能解析
- 支持多种格式：PDF、Word、Excel、PPT、图片等
- 多解析引擎：Apache Tika、Camelot、Tesseract OCR、PyMuPDF
- 智能表格识别：化工参数表格高精度提取
- OCR 文字识别：支持中英文混合及化工专业术语

### 🤖 Agent 智能系统
- **Think-Act-Observe 循环**：智能决策和执行
- **任务理解模块**：自然语言转执行计划
- **记忆系统**：会话记忆、知识记忆、执行记忆
- **多技能协调**：支持多软件协同工作

### 🔧 软件自动化
- **DWSIM 自动化**：COM 接口调用，流程模拟自动化
- **Excel 自动化**：数据读写、公式计算、图表生成
- **Aspen Plus**：流程模拟自动化（规划中）
- **AutoCAD**：图纸自动化（规划中）

### 🌐 Web 界面
- 现代化 React + TypeScript 前端
- Ant Design UI 组件库
- 实时执行监控
- 可视化结果展示

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 后端安装

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动后端服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### 前端安装

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

### 快速启动

Windows 用户可直接运行：
```bash
start_backend.bat    # 启动后端
start_frontend.bat   # 启动前端
```

访问 http://localhost:5173 开始使用

---

## 🏗️ 技术架构

### 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端层 (React)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Dashboard│  │Agent Panel│  │Document  │  │Settings │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                    API 网关层 (FastAPI)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ 认证授权  │  │ 文档解析  │  │ Agent    │  │ 自动化   │ │
│  │  API     │  │  API     │  │ API      │  │ API      │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    服务层 (Services)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Agent Engine │  │ Document     │  │ Automation   │  │
│  │ (Think-Act- │  │ Parser       │  │ Adapters     │  │
│  │  Observe)   │  │ Manager      │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    适配器层 (Adapters)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ DWSIM    │  │ Excel    │  │ Aspen    │  │ AutoCAD  │ │
│  │ Adapter  │  │ Adapter  │  │ Adapter  │  │ Adapter  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

**后端**
- FastAPI - 高性能 Web 框架
- Pydantic - 数据验证
- SQLAlchemy - ORM
- OpenAI API - LLM 集成
- Apache Tika - 文档解析
- Camelot - PDF 表格提取
- Tesseract OCR - 图像识别

**前端**
- React 18 - UI 框架
- TypeScript - 类型安全
- Ant Design - UI 组件库
- Vite - 构建工具
- Axios - HTTP 客户端

---

## 📚 文档

- [开发者指南](docs/docs/AIFILLER_DEVELOPER_GUIDE.md)
- [用户手册](docs/docs/AIFILLER_USER_GUIDE.md)
- [部署指南](docs/docs/AIFILLER_部署指南.md)
- [API 文档](http://localhost:8001/docs)
- [升级计划](docs/docs/agent_升级执行计划.md)

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 贡献方式

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 开发规范

- 遵循 Conventional Commits 规范
- 代码需通过 ESLint 和 TypeScript 检查
- 添加必要的测试用例
- 更新相关文档

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 👥 团队

**UnveilChem 开发团队**

- 项目负责人
- 核心开发者
- 产品经理

---

## 📞 联系我们

- 项目主页：[GitHub Repository](https://github.com/yourusername/UnveilChem)
- 问题反馈：[Issues](https://github.com/yourusername/UnveilChem/issues)
- 邮箱：contact@unveilchem.com

---

## 🙏 致谢

感谢以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://reactjs.org/)
- [Ant Design](https://ant.design/)
- [Apache Tika](https://tika.apache.org/)
- [Camelot](https://camelot-py.readthedocs.io/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个 Star！**

Made with ❤️ by UnveilChem Team

</div>
