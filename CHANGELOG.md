# 更新日志

本文档记录 UnveilChem 项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2026-03-07

### 新增

#### 核心功能
- 🚀 智能化工软件自动化平台初始版本发布
- 🤖 Agent 智能系统（Think-Act-Observe 循环）
- 📄 文档智能解析引擎
- 🔧 软件自动化适配器

#### 文档解析
- 支持 PDF、Word、Excel、PPT、图片等多种格式
- 集成 Apache Tika、Camelot、Tesseract OCR、PyMuPDF 解析引擎
- 智能表格识别和参数提取
- OCR 文字识别（支持中英文混合）

#### Agent 系统
- 任务理解模块（自然语言转执行计划）
- Agent 记忆系统（会话、知识、执行记忆）
- 多技能协调和跨软件协作
- Think-Act-Observe 智能循环

#### 软件自动化
- DWSIM COM 接口自动化
- Excel COM 接口自动化
- 软件自动发现和启动机制
- 参数化流程模拟

#### Web 界面
- React + TypeScript 前端应用
- Ant Design UI 组件库
- 实时执行监控面板
- 可视化结果展示
- 用户认证和权限管理

#### API 服务
- FastAPI 后端服务
- RESTful API 设计
- 自动 API 文档生成
- 文档上传和解析 API
- Agent 执行和监控 API

#### 项目架构
- Agent + Skill + Adapter 三层架构
- 模块化设计，易于扩展
- 统一的文档解析管理器
- 标准化的软件适配器接口

### 技术栈

**后端**
- Python 3.8+
- FastAPI
- Pydantic
- SQLAlchemy
- OpenAI API
- Apache Tika
- Camelot
- Tesseract OCR
- PyMuPDF

**前端**
- React 18
- TypeScript
- Ant Design
- Vite
- Axios

### 文档
- 开发者指南
- 用户手册
- 部署指南
- API 文档
- 贡献指南

---

## [Unreleased]

### 计划中

- Aspen Plus 自动化适配器
- AutoCAD 自动化适配器
- PRO/II 自动化适配器
- ChemCAD 自动化适配器
- 工作流编排引擎
- 数据流自动化
- 智能决策优化
- 错误处理和恢复机制

---

[1.0.0]: https://github.com/yourusername/UnveilChem/releases/tag/v1.0.0
