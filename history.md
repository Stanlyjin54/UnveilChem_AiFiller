# 版本历史

## 1.0.3 (2026-03-08)
- 修复文档管理页面：添加缺失的 report-templates 预览 API 路由
- 修复文档管理页面：在 ReportGenerator 类中添加 get_template_preview 方法
- 新增默认报告模板：创建 default.html 报告模板文件

## 1.0.2 (2026-03-08)
- 修复前端警告：修复 Dashboard.tsx 中 Table 数据源缺少 key 属性的警告
- 修复前端警告：修复 AgentPanel.tsx 中使用已弃用的 Tabs.TabPane 组件，改用 items 属性
- 修复前端警告：修复 LLMConfigPage.tsx 中 Select 组件 value 为 null 的警告

## 1.0.1 (2026-03-08)
- 修复智能对话功能：修复 LLM 配置加载问题，确保用户配置的 Ollama 模型可正确调用
- 修复 LLM 客户端获取逻辑：当 provider 为空时能正确获取默认客户端
- 优化模型名称匹配：支持部分模型名称匹配 Ollama 实际模型
- 更新数据库模型名称：从 qwen2.5 改为 qwen2.5:7b-instruct

## 1.0.0 (2026-03-07)
- 初始版本发布
- 实现智能化工软件自动化平台核心功能
- 支持 DWSIM COM 接口自动化
- 支持 Excel COM 接口自动化
- 实现 Agent 引擎 Think-Act-Observe 循环
- 实现软件自动发现功能
- 实现任务理解和执行计划生成
- 实现 Agent 记忆系统
- 更新项目定位为"智能化工软件自动化平台"
