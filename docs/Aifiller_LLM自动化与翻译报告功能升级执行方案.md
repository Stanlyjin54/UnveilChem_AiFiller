# Aifiller LLM自动化任务与翻译报告功能升级执行方案

## 一、方案概述

### 1.1 项目背景

本方案基于 `llm_app.py` 的LLM配置管理方式，结合 `项目架构设计.md` 中的LLM自动化任务可行性方案，形成一套完整的项目升级执行计划。核心思路是：**复用现有LLM配置体系，降低用户配置成本，提供更友好的使用体验**。

### 1.2 设计理念

| 原方案（参考OpenClaw） | 改进方案（参考llm_app.py） |
|----------------------|--------------------------|
| 独立配置翻译/报告API | 复用已配置的LLM |
| 需要额外部署翻译模型 | 使用用户已有的LLM（GPT-4/Claude等） |
| 独立的术语库管理 | 通过System Prompt控制翻译质量 |
| 复杂的模型部署流程 | 用户只需配置一次API Key |

### 1.3 核心优势

1. **用户友好**：用户只需配置一次LLM（通过llm_app.py的方式），即可用于翻译、报告生成、自动化任务
2. **成本优化**：复用现有LLM资源，无需额外付费翻译API
3. **质量可控**：通过精心设计的Prompt保证翻译和报告质量
4. **易于维护**：统一的服务架构，便于后续扩展

---

## 二、系统架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              前端层 (admin-frontend)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  LLM配置页面 │  │ 任务控制面板 │  │ 翻译功能页  │  │ 报告生成页  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           API层 (backend/app/api)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  llm_app.py │  │automation.py│  │translation.py│ │ report_api.py│  │
│  │ (LLM配置管理)│  │(自动化任务)  │  │ (翻译API)   │  │(报告生成API)│  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          服务层 (backend/app/services)                  │
│  ┌─────────────────────────────┐  ┌─────────────────────────────────┐ │
│  │     Agent Orchestration     │  │      Translation Service        │ │
│  │  ┌───────────────────────┐  │  │  ┌───────────────────────────┐  │ │
│  │  │ AgentService          │  │  │  │ LLMTranslationService    │  │ │
│  │  │ - Intent Recognition │  │  │  │ - Prompt Templates       │  │ │
│  │  │ - Parameter Extraction│  │  │  │ - Translation Cache      │  │ │
│  │  │ - Tool Selection      │  │  │  └───────────────────────────┘  │ │
│  │  └───────────────────────┘  │  └─────────────────────────────────┘ │
│  │  ┌───────────────────────┐  │  ┌─────────────────────────────────┐ │
│  │  │ ToolOrchestrator      │  │  │      Report Service             │ │
│  │  │ - Workflow Planning   │  │  │  ┌───────────────────────────┐  │ │
│  │  │ - Task Coordination   │  │  │  │ LLMReportGenerator       │  │ │
│  │  │ - Error Recovery      │  │  │  │ - Report Templates        │  │ │
│  │  └───────────────────────┘  │  │  │ - Data Visualization      │  │ │
│  └─────────────────────────────┘  │  └───────────────────────────┘  │ │
│                                    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       LLM适配层 (rag.llm)                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  ChatModel  │  │EmbeddingModel│ │RerankModel  │  │   CvModel   │  │
│  │  (对话模型)  │  │  (Embedding) │ │  (重排序)   │  │ (图像理解)  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
│                                                                        │
│  支持: OpenAI, Claude, Azure-OpenAI, Ollama, LocalAI, Gemini等         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       自动化引擎层 (AutomationEngine)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │AspenPlusAdapter│ │ DWSIMAdapter│ │ AutoCADAdapter│ │ ExcelAdapter│  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流设计

```
用户请求 (自然语言)
       │
       ▼
┌──────────────────┐
│  AgentService   │
│  意图识别        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│ 参数提取器       │────▶│ LLM (已配置)     │
│ (LLM驱动)        │     │ 生成执行计划     │
└────────┬─────────┘     └──────────────────┘
         │
         ▼
┌──────────────────┐
│ ToolOrchestrator│
│ 工具编排        │
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐  ┌───────┐
│ 翻译  │  │ 报告  │
│ 服务  │  │ 生成  │
└───────┘  └───────┘
    │         │
    └────┬────┘
         ▼
┌──────────────────┐
│  执行结果返回    │
└──────────────────┘
```

---

## 三、LLM配置管理（复用llm_app.py）

### 3.1 现有LLM配置机制分析

`llm_app.py` 提供了完整的LLM配置管理功能：

| 功能 | 实现方式 | 说明 |
|-----|--------|-----|
| API Key设置 | `/set_api_key` | 测试API可用性后保存 |
| 添加LLM | `/add_llm` | 支持多种LLM厂商 |
| 删除LLM | `/delete_llm` | 按厂商/模型删除 |
| 启用/禁用 | `/enable_llm` | 控制LLM可用性 |
| 获取LLM列表 | `/my_llms` | 获取用户已配置的LLM |
| 获取可用LLM | `/list` | 获取系统支持的LLM |

### 3.2 扩展设计

在现有LLM配置基础上，增加以下功能：

```python
# backend/app/schemas/llm.py (新增)

from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class LLMUsageType(str, Enum):
    """LLM用途枚举"""
    CHAT = "chat"              # 对话
    TRANSLATION = "translation"  # 翻译
    REPORT = "report"          # 报告生成
    AGENT = "agent"            # Agent任务

class LLMConfigUpdate(BaseModel):
    """LLM配置更新"""
    llm_factory: str
    llm_name: str
    usage_types: List[LLMUsageType] = [LLMUsageType.CHAT]
    translation_prompt: Optional[str] = None  # 自定义翻译提示词
    report_prompt: Optional[str] = None       # 自定义报告提示词
```

### 3.3 前端集成

复用现有的LLM管理界面，增加用途配置：

```
┌────────────────────────────────────────────────────────────┐
│  LLM配置管理                                               │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌────────────────┐  ┌────────────────┐                   │
│  │ 可用LLM列表    │  │ 我的LLM配置    │                   │
│  │                │  │                │                   │
│  │ ○ OpenAI      │  │ ✓ GPT-4        │                   │
│  │   - gpt-4     │  │   用途: 对话   │                   │
│  │   - gpt-3.5  │  │   用途: 翻译   │                   │
│  │                │  │   用途: 报告   │                   │
│  │ ○ Claude      │  │                │                   │
│  │   - claude-3  │  │ ✓ Claude-3     │                   │
│  │                │  │   用途: Agent  │                   │
│  └────────────────┘  └────────────────┘                   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 四、核心模块详细设计

### 4.1 Agent Service (代理服务)

```python
# backend/app/services/agent/agent_service.py

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel
import json
import logging

logger = logging.getLogger(__name__)

class TaskIntent(Enum):
    """任务意图枚举"""
    PARAMETER_EXTRACTION = "parameter_extraction"  # 参数提取
    SIMULATION_RUN = "simulation_run"              # 运行模拟
    REPORT_GENERATION = "report_generation"        # 报告生成
    DOCUMENT_TRANSLATION = "document_translation"  # 文档翻译
    SOFTWARE_OPERATION = "software_operation"      # 软件操作
    GENERAL_CHAT = "general_chat"                  # 一般对话

class AgentRequest(BaseModel):
    """代理请求"""
    user_input: str
    context: Dict[str, Any] = {}
    attachments: List[str] = []  # 文件路径
    target_software: Optional[str] = None
    llm_factory: Optional[str] = None  # 指定使用的LLM
    usage_type: str = "agent"  # agent/translation/report

class AgentResponse(BaseModel):
    """代理响应"""
    intent: TaskIntent
    confidence: float
    extracted_parameters: Dict[str, Any] = {}
    suggested_actions: List[Dict[str, Any]] = []
    execution_plan: Optional[Dict[str, Any]] = None
    response_text: Optional[str] = None

class AgentService:
    """LLM代理服务 - 复用已配置的LLM"""
    
    def __init__(self):
        self.llm_clients: Dict[str, Any] = {}
        self.intent_classifier = None
        self.parameter_extractor = None
        
    def get_llm_client(self, factory: str = None) -> Any:
        """获取LLM客户端 - 参考llm_app.py的配置"""
        # 复用 llm_app.py 中的LLM配置
        # 从TenantLLMService获取用户配置的LLM
        pass
    
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """处理用户请求"""
        
        # Step 1: 意图识别
        intent = await self._classify_intent(request.user_input)
        
        # Step 2: 参数提取
        extracted_params = await self._extract_parameters(
            request.user_input,
            request.attachments,
            intent
        )
        
        # Step 3: 根据意图处理
        if intent == TaskIntent.DOCUMENT_TRANSLATION:
            return await self._handle_translation(request, extracted_params)
        elif intent == TaskIntent.REPORT_GENERATION:
            return await self._handle_report_generation(request, extracted_params)
        else:
            # Step 4: 生成执行计划
            execution_plan = await self._generate_execution_plan(
                intent,
                extracted_params,
                request.target_software
            )
            
        return AgentResponse(
            intent=intent,
            confidence=0.9,
            extracted_parameters=extracted_params,
            suggested_actions=execution_plan.get("actions", []) if execution_plan else [],
            execution_plan=execution_plan
        )
    
    async def _classify_intent(self, user_input: str) -> TaskIntent:
        """意图识别 - 使用LLM"""
        prompt = f"""
你是一个意图分类专家。根据用户输入，判断用户的意图。

可能的意图：
- parameter_extraction: 从文档中提取参数
- simulation_run: 运行化工模拟
- report_generation: 生成报告
- document_translation: 翻译文档
- software_operation: 操作软件
- general_chat: 一般对话

用户输入：{user_input}

请直接返回意图名称，不要有其他内容：
"""
        # 调用LLM进行意图分类
        response = await self._call_llm(prompt, usage_type="agent")
        # 解析响应...
        return TaskIntent.GENERAL_CHAT
    
    async def _call_llm(self, prompt: str, usage_type: str = "agent") -> str:
        """调用LLM - 复用llm_app.py的配置"""
        # 1. 从TenantLLMService获取可用的LLM
        # 2. 根据usage_type选择合适的LLM
        # 3. 调用ChatModel进行对话
        pass
```

### 4.2 Translation Service (翻译服务)

```python
# backend/app/services/translation/translation_service.py

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

class TranslationRequest(BaseModel):
    """翻译请求"""
    text: str
    source_lang: str = "auto"  # auto/en/zh/es/ja/ko/fr/de
    target_lang: str = "zh"
    llm_factory: Optional[str] = None  # 指定LLM
    use_cache: bool = True
    style: str = "professional"  # professional/casual/technical

class TranslationResponse(BaseModel):
    """翻译响应"""
    translated_text: str
    source_lang: str
    target_lang: str
    confidence: float = 1.0
    cached: bool = False

class LLMTranslationService:
    """基于LLM的翻译服务 - 复用llm_app.py的LLM配置"""
    
    # 翻译提示词模板
    TRANSLATION_PROMPTS = {
        "professional": """你是一个专业的化工领域翻译专家。请将以下文本翻译成{target_lang}。
要求：
1. 保持专业术语的准确性
2. 译文流畅自然
3. 保持原文格式
4. 如果遇到不确定的术语，保留英文并在括号中说明

原文：
{text}

译文：""",

        "technical": """你是一个技术文档翻译专家。请将以下技术文档翻译成{target_lang}。
要求：
1. 准确翻译技术术语
2. 保持代码和公式格式
3. 使用准确的技术用语
4. 如果遇到不确定的术语，保留英文

原文：
{text}

译文：""",

        "casual": """请将以下文本翻译成{target_lang}。
要求：
1. 译文自然流畅
2. 符合目标语言的口语习惯

原文：
{text}

译文："""
    }
    
    def __init__(self):
        self.cache: Dict[str, TranslationResponse] = {}
        self.llm_service = None  # 注入LLM服务
        
    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        """执行翻译"""
        
        # 1. 检查缓存
        if request.use_cache:
            cache_key = self._get_cache_key(request)
            if cache_key in self.cache:
                cached = self.cache[cache_key]
                cached.cached = True
                return cached
                
        # 2. 获取LLM客户端 (复用llm_app.py配置)
        llm_client = await self._get_llm_client(request.llm_factory)
        
        # 3. 构建提示词
        prompt = self._build_prompt(request)
        
        # 4. 调用LLM翻译
        response = await llm_client.chat(prompt)
        
        # 5. 处理结果
        result = TranslationResponse(
            translated_text=response,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            confidence=0.95
        )
        
        # 6. 存入缓存
        if request.use_cache:
            self.cache[cache_key] = result
            
        return result
    
    async def translate_document(
        self, 
        document_content: str,
        target_lang: str = "zh",
        llm_factory: str = None,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """翻译整个文档"""
        
        # 分段处理长文本
        segments = self._split_text(document_content)
        results = []
        
        for i, segment in enumerate(segments):
            request = TranslationRequest(
                text=segment,
                target_lang=target_lang,
                llm_factory=llm_factory
            )
            result = await self.translate(request)
            results.append(result.translated_text)
            
            if progress_callback:
                progress_callback((i + 1) / len(segments))
                
        return "\n".join(results)
    
    def _build_prompt(self, request: TranslationRequest) -> str:
        """构建翻译提示词"""
        template = self.TRANSLATION_PROMPTS.get(request.style, self.TRANSLATION_PROMPTS["professional"])
        return template.format(
            target_lang=self._get_lang_name(request.target_lang),
            text=request.text
        )
    
    async def _get_llm_client(self, factory: str = None):
        """获取LLM客户端 - 复用llm_app.py"""
        # 从TenantLLMService获取用户配置的LLM
        # 确保该LLM支持CHAT类型
        pass
    
    def _get_cache_key(self, request: TranslationRequest) -> str:
        """生成缓存键"""
        content = f"{request.text}:{request.source_lang}:{request.target_lang}:{request.style}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _split_text(self, text: str, max_length: int = 2000) -> List[str]:
        """分段处理长文本"""
        # 按段落和句子分割
        pass
    
    def _get_lang_name(self, code: str) -> str:
        """语言代码转名称"""
        lang_map = {"zh": "中文", "en": "英文", "ja": "日文", "ko": "韩文"}
        return lang_map.get(code, code)
```

### 4.3 Report Service (报告生成服务)

```python
# backend/app/services/report/report_service.py

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel
import json
import logging

logger = logging.getLogger(__name__)

class ReportType(str, Enum):
    """报告类型"""
    PARAMETER_SUMMARY = "parameter_summary"      # 参数汇总
    SIMULATION_RESULT = "simulation_result"       # 模拟结果
    DATA_COMPARISON = "data_comparison"            # 数据对比
    LITERATURE_REVIEW = "literature_review"       # 文献综述
    CUSTOM = "custom"                              # 自定义

class ReportFormat(str, Enum):
    """报告格式"""
    PDF = "pdf"
    WORD = "word"
    HTML = "html"
    MARKDOWN = "markdown"

class ReportRequest(BaseModel):
    """报告生成请求"""
    report_type: ReportType
    source_data: Dict[str, Any]  # 解析的文档数据
    template: Optional[str] = None
    format: ReportFormat = ReportFormat.PDF
    llm_factory: Optional[str] = None
    title: Optional[str] = None
    custom_sections: Optional[List[str]] = None

class ReportResponse(BaseModel):
    """报告生成响应"""
    report_id: str
    content: str
    format: ReportFormat
    download_url: Optional[str] = None

class LLMReportGenerator:
    """基于LLM的报告生成器"""
    
    # 报告提示词模板
    REPORT_PROMPTS = {
        ReportType.PARAMETER_SUMMARY: """你是一个化工技术文档专家。请根据以下解析的文档内容，生成一份参数汇总报告。

要求：
1. 提取并汇总所有关键参数
2. 按类别分组展示
3. 提供参数单位换算（如需要）
4. 使用表格清晰展示

原始数据：
{data}

参数汇总报告：""",

        ReportType.SIMULATION_RESULT: """你是一个化工模拟专家。请根据以下模拟结果数据，生成一份详细的模拟结果报告。

要求：
1. 总结模拟的关键结果
2. 分析数据趋势
3. 指出需要注意的问题
4. 提供专业建议

模拟数据：
{data}

模拟结果报告：""",

        ReportType.DATA_COMPARISON: """你是一个数据分析专家。请根据以下数据，生成一份数据对比报告。

要求：
1. 对比各项数据的差异
2. 使用表格和图表展示对比结果
3. 分析差异原因
4. 提供改进建议

对比数据：
{data}

数据对比报告："""
    }
    
    def __init__(self):
        self.llm_service = None
        self.template_cache = {}
        
    async def generate_report(self, request: ReportRequest) -> ReportResponse:
        """生成报告"""
        
        # 1. 获取LLM客户端
        llm_client = await self._get_llm_client(request.llm_factory)
        
        # 2. 准备数据
        data = self._prepare_data(request)
        
        # 3. 构建提示词
        prompt = self._build_prompt(request, data)
        
        # 4. 调用LLM生成报告
        report_content = await llm_client.chat(prompt)
        
        # 5. 转换为目标格式
        final_content = await self._format_report(report_content, request.format)
        
        return ReportResponse(
            report_id=self._generate_report_id(),
            content=final_content,
            format=request.format
        )
    
    async def generate_with_template(
        self, 
        request: ReportRequest,
        template_content: str
    ) -> ReportResponse:
        """使用自定义模板生成报告"""
        
        # 1. 解析模板，提取占位符
        placeholders = self._extract_placeholders(template_content)
        
        # 2. 使用LLM填充占位符
        filled_content = await self._fill_template_with_llm(
            template_content, 
            placeholders,
            request.source_data
        )
        
        # 3. 转换为目标格式
        final_content = await self._format_report(filled_content, request.format)
        
        return ReportResponse(
            report_id=self._generate_report_id(),
            content=final_content,
            format=request.format
        )
    
    def _build_prompt(self, request: ReportRequest, data: str) -> str:
        """构建报告生成提示词"""
        template = self.REPORT_PROMPTS.get(
            request.report_type, 
            self.REPORT_PROMPTS[ReportType.PARAMETER_SUMMARY]
        )
        
        prompt = template.format(data=json.dumps(data, ensure_ascii=False, indent=2))
        
        if request.title:
            prompt = f"# {request.title}\n\n" + prompt
            
        if request.custom_sections:
            prompt += f"\n\n请包含以下章节：{', '.join(request.custom_sections)}"
            
        return prompt
    
    async def _get_llm_client(self, factory: str = None):
        """获取LLM客户端 - 复用llm_app.py"""
        pass
    
    async def _format_report(self, content: str, format: ReportFormat) -> str:
        """格式化报告"""
        # 根据格式进行转换
        pass
    
    def _prepare_data(self, request: ReportRequest) -> Dict[str, Any]:
        """准备数据"""
        # 从source_data中提取需要的信息
        pass
    
    def _extract_placeholders(self, template: str) -> List[str]:
        """提取模板占位符"""
        import re
        return re.findall(r'\{\{(\w+)\}\}', template)
    
    async def _fill_template_with_llm(
        self, 
        template: str, 
        placeholders: List[str],
        data: Dict[str, Any]
    ) -> str:
        """使用LLM填充模板占位符"""
        pass
    
    def _generate_report_id(self) -> str:
        """生成报告ID"""
        import uuid
        return f"report_{uuid.uuid4().hex}"
```

### 4.4 Tool Orchestrator (工具编排器)

```python
# backend/app/services/agent/tool_orchestrator.py

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)

class ToolType(Enum):
    """工具类型"""
    DOCUMENT_PARSER = "document_parser"     # 文档解析
    TRANSLATION = "translation"              # 翻译
    REPORT_GENERATOR = "report_generator"   # 报告生成
    SIMULATION = "simulation"               # 模拟软件
    PARAMETER_MAPPER = "parameter_mapper"   # 参数映射
    DATA_PROCESSOR = "data_processor"       # 数据处理

@dataclass
class ToolExecution:
    """工具执行描述"""
    tool_name: str
    tool_type: ToolType
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)  # 依赖的其他工具
    retry_on_failure: bool = True
    max_retries: int = 3

@dataclass
class ExecutionStep:
    """执行步骤"""
    step_id: str
    tool: ToolExecution
    status: str = "pending"  # pending/running/completed/failed
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

class ToolOrchestrator:
    """工具编排器 - 协调各服务完成复杂任务"""
    
    def __init__(self):
        self.tools: Dict[str, Any] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self._register_tools()
        
    def _register_tools(self):
        """注册可用工具"""
        self.tools = {
            "document_parser": {
                "handler": self._execute_document_parser,
                "description": "文档解析",
                "supported_types": ["pdf", "docx", "xlsx", "txt"]
            },
            "translation": {
                "handler": self._execute_translation,
                "description": "文档翻译",
                "supported_langs": ["en", "zh", "ja", "ko", "fr", "de"]
            },
            "report_generator": {
                "handler": self._execute_report_generator,
                "description": "报告生成",
                "supported_formats": ["pdf", "word", "html", "markdown"]
            },
            "aspen_plus": {
                "handler": self._execute_aspen_plus,
                "description": "Aspen Plus模拟",
                "parameters": ["simulation_file", "parameters"]
            },
            "dwsim": {
                "handler": self._execute_dwsim,
                "description": "DWSIM模拟",
                "parameters": ["flowsheet", "parameters"]
            },
            "parameter_mapper": {
                "handler": self._map_parameters,
                "description": "参数映射转换",
                "source_software": "auto",
                "target_software": "auto"
            }
        }
        
    async def execute_plan(
        self, 
        execution_plan: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """执行完整的执行计划"""
        
        results = {}
        steps = []
        
        # 解析执行计划
        for i, step_config in enumerate(execution_plan.get("steps", [])):
            step = ExecutionStep(
                step_id=step_config.get("id", f"step_{i}"),
                tool=ToolExecution(
                    tool_name=step_config["tool"],
                    tool_type=ToolType(step_config.get("type", "data_processor")),
                    parameters=step_config.get("parameters", {}),
                    dependencies=step_config.get("dependencies", [])
                )
            )
            steps.append(step)
            
        # 按依赖顺序执行
        for step in steps:
            # 检查依赖是否满足
            if not self._check_dependencies(step.tool.dependencies, results):
                step.status = "failed"
                step.error = f"依赖未满足: {step.tool.dependencies}"
                continue
                
            # 执行工具
            try:
                step.status = "running"
                step.start_time = asyncio.get_event_loop().time()
                
                result = await self._execute_tool(
                    step.tool.tool_name,
                    step.tool.parameters,
                    results  # 传入前面步骤的结果
                )
                
                step.status = "completed"
                step.result = result
                results[step.step_id] = result
                
            except Exception as e:
                step.status = "failed"
                step.error = str(e)
                logger.error(f"工具执行失败: {step.tool.tool_name}, 错误: {e}")
                
                if not step.tool.retry_on_failure:
                    continue
                    
                # 重试逻辑
                for retry in range(step.tool.max_retries):
                    try:
                        result = await self._execute_tool(
                            step.tool.tool_name,
                            step.tool.parameters,
                            results
                        )
                        step.status = "completed"
                        step.result = result
                        results[step.step_id] = result
                        break
                    except Exception as retry_error:
                        logger.warning(f"重试 {retry + 1}/{step.tool.max_retries} 失败")
                        continue
                        
            if progress_callback:
                progress_callback(len([s for s in steps if s.status == "completed"]) / len(steps))
                
        return {
            "status": "completed" if all(s.status == "completed" for s in steps) else "partial",
            "results": results,
            "steps": [
                {
                    "id": s.step_id,
                    "tool": s.tool.tool_name,
                    "status": s.status,
                    "error": s.error
                }
                for s in steps
            ]
        }
    
    async def _execute_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Any:
        """执行单个工具"""
        
        if tool_name not in self.tools:
            raise ValueError(f"未知工具: {tool_name}")
            
        tool_handler = self.tools[tool_name]["handler"]
        return await tool_handler(parameters, context)
    
    async def _execute_document_parser(
        self, 
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行文档解析"""
        from ..document_parser import DocumentParser
        
        parser = DocumentParser()
        file_path = parameters.get("file_path")
        file_type = parameters.get("file_type", "pdf")
        
        result = await parser.parse(file_path, file_type)
        return result
    
    async def _execute_translation(
        self, 
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行翻译"""
        from ..translation.translation_service import LLMTranslationService
        
        service = LLMTranslationService()
        
        text = parameters.get("text") or context.get("parsed_content", "")
        target_lang = parameters.get("target_lang", "zh")
        
        result = await service.translate_document(
            text,
            target_lang=target_lang
        )
        
        return {"translated_text": result}
    
    async def _execute_report_generator(
        self, 
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行报告生成"""
        from ..report.report_service import LLMReportGenerator
        
        generator = LLMReportGenerator()
        
        source_data = parameters.get("source_data") or context
        report_type = parameters.get("report_type", "parameter_summary")
        
        result = await generator.generate_report({
            "report_type": report_type,
            "source_data": source_data
        })
        
        return {"report_content": result.content}
    
    async def _execute_aspen_plus(
        self, 
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行Aspen Plus模拟"""
        # 调用自动化引擎
        pass
    
    async def _execute_dwsim(
        self, 
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行DWSIM模拟"""
        # 调用自动化引擎
        pass
    
    async def _map_parameters(
        self, 
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """参数映射"""
        source = parameters.get("source_software")
        target = parameters.get("target_software")
        params = parameters.get("parameters", {})
        
        # 使用LLM进行参数映射
        mapped = await self._llm_map_parameters(source, target, params)
        return mapped
    
    async def _llm_map_parameters(
        self, 
        source: str, 
        target: str, 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用LLM进行参数映射"""
        prompt = f"""
你是一个化工软件参数映射专家。请将以下从{source}软件的参数映射到{target}软件。

源参数：
{json.dumps(params, ensure_ascii=False)}

请返回映射后的参数，使用{target}软件的参数名称：
"""
        # 调用LLM
        pass
    
    def _check_dependencies(
        self, 
        dependencies: List[str], 
        results: Dict[str, Any]
    ) -> bool:
        """检查依赖是否满足"""
        for dep in dependencies:
            if dep not in results:
                return False
        return True
```

---

## 五、API设计

### 5.1 新增API端点

```python
# backend/app/api/agent_api.py (新增)

from quart import Blueprint, request, jsonify
from ...utils.api_utils import login_required, get_json_result
from ..services.agent.agent_service import AgentService, AgentRequest, TaskIntent

agent_bp = Blueprint('agent', __name__, url_prefix='/api/agent')

@agent_bp.route('/process', methods=['POST'])
@login_required
async def process_request():
    """处理用户请求"""
    req = await request.get_json()
    
    agent = AgentService()
    response = await agent.process_request(AgentRequest(**req))
    
    return get_json_result(data=response.dict())

@agent_bp.route('/intents', methods=['GET'])
@login_required
def list_intents():
    """获取支持的意图类型"""
    intents = [
        {"name": intent.name, "value": intent.value}
        for intent in TaskIntent
    ]
    return get_json_result(data=intents)
```

```python
# backend/app/api/translation_api.py (新增)

from quart import Blueprint, request, jsonify
from ...utils.api_utils import login_required, get_json_result
from ..services.translation.translation_service import (
    LLMTranslationService, 
    TranslationRequest
)

translation_bp = Blueprint('translation', __name__, url_prefix='/api/translation')

@translation_bp.route('/translate', methods=['POST'])
@login_required
async def translate_text():
    """翻译文本"""
    req = await request.get_json()
    
    service = LLMTranslationService()
    result = await service.translate(TranslationRequest(**req))
    
    return get_json_result(data=result.dict())

@translation_bp.route('/document', methods=['POST'])
@login_required
async def translate_document():
    """翻译文档"""
    req = await request.get_json()
    file_path = req.get("file_path")
    target_lang = req.get("target_lang", "zh")
    
    # 1. 解析文档
    # 2. 翻译内容
    # 3. 返回结果
    
    return get_json_result(data={"translated_content": "..."})
```

```python
# backend/app/api/report_api.py (新增)

from quart import Blueprint, request, jsonify
from ...utils.api_utils import login_required, get_json_result
from ..services.report.report_service import (
    LLMReportGenerator, 
    ReportRequest,
    ReportType,
    ReportFormat
)

report_bp = Blueprint('report', __name__, url_prefix='/api/report')

@report_bp.route('/generate', methods=['POST'])
@login_required
async def generate_report():
    """生成报告"""
    req = await request.get_json()
    
    generator = LLMReportGenerator()
    result = await generator.generate_report(ReportRequest(**req))
    
    return get_json_result(data=result.dict())

@report_bp.route('/templates', methods=['GET'])
@login_required
def list_templates():
    """获取报告模板列表"""
    templates = [
        {"id": "parameter_summary", "name": "参数汇总报告", "type": ReportType.PARAMETER_SUMMARY},
        {"id": "simulation_result", "name": "模拟结果报告", "type": ReportType.SIMULATION_RESULT},
        {"id": "data_comparison", "name": "数据对比报告", "type": ReportType.DATA_COMPARISON}
    ]
    return get_json_result(data=templates)
```

### 5.2 现有API扩展

```python
# 扩展 llm_app.py 中的 /my_llms 端点

@manager.route("/my_llms", methods=["GET"])
@login_required
def my_llms():
    # ... 现有代码 ...
    
    # 新增：返回LLM支持的用途
    for o in objs:
        o_dict = o.to_dict()
        # 判断该LLM支持哪些用途
        o_dict["supported_usages"] = _get_supported_usages(o_dict)
        # ...
```

---

## 六、前端设计

### 6.1 页面结构

```
src/
├── pages/
│   ├── Agent/                    # Agent任务页面
│   │   ├── AgentPanel.tsx       # Agent控制面板
│   │   ├── TaskHistory.tsx      # 任务历史
│   │   └── IntentConfig.tsx     # 意图配置
│   ├── Translation/             # 翻译功能页面
│   │   ├── TranslationPanel.tsx # 翻译面板
│   │   ├── DocumentTranslate.tsx # 文档翻译
│   │   └── TranslationSettings.tsx # 翻译设置
│   ├── Report/                  # 报告生成页面
│   │   ├── ReportPanel.tsx      # 报告面板
│   │   ├── TemplateSelect.tsx   # 模板选择
│   │   └── ReportPreview.tsx    # 报告预览
│   └── LLM/                     # 复用现有LLM配置
│       ├── LLMList.tsx          # LLM列表
│       ├── LLMConfig.tsx        # LLM配置
│       └── LLMUsage.tsx         # 用途配置(新增)
```

### 6.2 组件设计

```typescript
// src/pages/Agent/AgentPanel.tsx

import React, { useState } from 'react';
import { Card, Input, Button, Select, Spin, message } from 'antd';
import { SendOutlined, RobotOutlined } from '@ant-design/icons';
import { agentAPI } from '../../services/api';

const { TextArea } = Input;
const { Option } = Select;

interface AgentResponse {
  intent: string;
  confidence: number;
  extracted_parameters: Record<string, any>;
  suggested_actions: Array<{ label: string; action: string }>;
  execution_plan: Record<string, any>;
}

export const AgentPanel: React.FC = () => {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<AgentResponse | null>(null);

  const handleSubmit = async () => {
    if (!input.trim()) return;
    
    setLoading(true);
    try {
      const res = await agentAPI.process({
        user_input: input,
        // 可以指定使用的LLM
        llm_factory: 'OpenAI',
        usage_type: 'agent'
      });
      setResponse(res.data);
    } catch (error) {
      message.error('处理请求失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="agent-panel">
      <Card 
        title={<><RobotOutlined /> Agent 控制面板</>}
        extra={<Select defaultValue="OpenAI" style={{ width: 120 }}><Option value="OpenAI">GPT-4</Option><Option value="Claude">Claude</Option></Select>}
      >
        <TextArea 
          rows={4} 
          placeholder="输入您的需求，如：从这个PDF提取参数并生成报告"
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        
        <div style={{ marginTop: 16 }}>
          <Button 
            type="primary" 
            icon={<SendOutlined />}
            onClick={handleSubmit}
            loading={loading}
          >
            执行
          </Button>
        </div>
        
        {loading && <Spin tip="处理中..." />}
        
        {response && (
          <div className="response-section">
            <h4>识别意图: {response.intent}</h4>
            <p>置信度: {(response.confidence * 100).toFixed(1)}%</p>
            
            {response.extracted_parameters && (
              <div>
                <h4>提取的参数:</h4>
                <pre>{JSON.stringify(response.extracted_parameters, null, 2)}</pre>
              </div>
            )}
            
            {response.execution_plan && (
              <div>
                <h4>执行计划:</h4>
                <pre>{JSON.stringify(response.execution_plan, null, 2)}</pre>
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
};
```

```typescript
// src/pages/Translation/TranslationPanel.tsx

import React, { useState } from 'react';
import { Card, Select, Button, Input, Spin, message } from 'antd';
import { TranslationOutlined } from '@ant-design/icons';
import { translationAPI } from '../../services/api';
import { useLLMConfig } from '../../contexts/LLMContext'; // 复用LLM配置

const { TextArea } = Input;
const { Option } = Select;

export const TranslationPanel: React.FC = () => {
  const [sourceText, setSourceText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [targetLang, setTargetLang] = useState('zh');
  const [style, setStyle] = useState('professional');
  const [loading, setLoading] = useState(false);
  
  // 获取用户已配置的LLM列表
  const { configuredLLMs } = useLLMConfig();
  const llmOptions = configuredLLMs.filter(llm => 
    llm.usage_types.includes('translation')
  );

  const handleTranslate = async () => {
    if (!sourceText.trim()) return;
    
    setLoading(true);
    try {
      const res = await translationAPI.translate({
        text: sourceText,
        target_lang: targetLang,
        style: style,
        llm_factory: llmOptions[0]?.factory
      });
      setTranslatedText(res.data.translated_text);
    } catch (error) {
      message.error('翻译失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title={<><TranslationOutlined /> 文档翻译</>}>
      <div className="translation-container">
        <div className="source-section">
          <h4>原文</h4>
          <TextArea 
            rows={10}
            value={sourceText}
            onChange={(e) => setSourceText(e.target.value)}
            placeholder="输入需要翻译的内容..."
          />
        </div>
        
        <div className="controls">
          <Select value={targetLang} onChange={setTargetLang} style={{ width: 100 }}>
            <Option value="zh">中文</Option>
            <Option value="en">英文</Option>
            <Option value="ja">日文</Option>
            <Option value="ko">韩文</Option>
          </Select>
          
          <Select value={style} onChange={setStyle} style={{ width: 120 }}>
            <Option value="professional">专业</Option>
            <Option value="technical">技术</Option>
            <Option value="casual">口语</Option>
          </Select>
          
          <Select 
            placeholder="选择LLM" 
            style={{ width: 150 }}
            disabled={llmOptions.length === 0}
          >
            {llmOptions.map(llm => (
              <Option key={llm.factory} value={llm.factory}>
                {llm.factory} - {llm.model_name}
              </Option>
            ))}
          </Select>
          
          <Button 
            type="primary" 
            onClick={handleTranslate}
            loading={loading}
          >
            翻译
          </Button>
        </div>
        
        <div className="target-section">
          <h4>译文</h4>
          <TextArea 
            rows={10}
            value={translatedText}
            readOnly
            placeholder="翻译结果将显示在这里..."
          />
        </div>
      </div>
      
      {loading && <Spin tip="翻译中..." />}
    </Card>
  );
};
```

---

## 七、实施计划

### 7.1 阶段划分

| 阶段 | 时间 | 任务 | 产出 |
|-----|-----|------|------|
| **Phase 1** | 第1-2周 | LLM配置集成 | 复用llm_app.py，新增用途配置 |
| **Phase 2** | 第3-5周 | Agent核心服务 | 意图识别、参数提取、执行计划 |
| **Phase 3** | 第6-8周 | 翻译服务 | 文本/文档翻译、缓存优化 |
| **Phase 4** | 第9-11周 | 报告服务 | 模板生成、多格式输出 |
| **Phase 5** | 第12-14周 | 工具编排 | 多软件协调、错误恢复 |
| **Phase 6** | 第15-16周 | 前端集成与测试 | 完整功能、用户体验优化 |

### 7.2 详细任务分解

#### Phase 1: LLM配置集成 (第1-2周)

| 任务 | 说明 | 负责人 | 
|-----|------|-------|
| T1.1 | 分析llm_app.py的LLM配置机制 | - |
| T1.2 | 扩展TenantLLM模型，添加用途字段 | - |
| T1.3 | 修改LLM管理API，支持用途配置 | - |
| T1.4 | 前端LLM配置页面增加用途选择 | - |
| T1.5 | 编写单元测试 | - |

#### Phase 2: Agent核心服务 (第3-5周)

| 任务 | 说明 | 负责人 |
|-----|------|-------|
| T2.1 | 创建AgentService基础框架 | - |
| T2.2 | 实现意图识别模块 | - |
| T2.3 | 实现LLM参数提取器 | - |
| T2.4 | 实现执行计划生成器 | - |
| T2.5 | 创建Agent API端点 | - |
| T2.6 | 前端Agent面板开发 | - |

#### Phase 3: 翻译服务 (第6-8周)

| 任务 | 说明 | 负责人 |
|-----|------|-------|
| T3.1 | 创建TranslationService | - |
| T3.2 | 实现翻译提示词模板 | - |
| T3.3 | 实现翻译缓存机制 | - |
| T3.4 | 实现文档翻译（分段处理） | - |
| T3.5 | 创建Translation API端点 | - |
| T3.6 | 前端翻译面板开发 | - |

#### Phase 4: 报告服务 (第9-11周)

| 任务 | 说明 | 负责人 |
|-----|------|-------|
| T4.1 | 创建ReportService | - |
| T4.2 | 实现报告模板系统 | - |
| T4.3 | 实现LLM报告生成 | - |
| T4.4 | 实现多格式输出(PDF/Word) | - |
| T4.5 | 创建Report API端点 | - |
| T4.6 | 前端报告面板开发 | - |

#### Phase 5: 工具编排 (第12-14周)

| 任务 | 说明 | 负责人 |
|-----|------|-------|
| T5.1 | 创建ToolOrchestrator | - |
| T5.2 | 实现工作流编排 | - |
| T5.3 | 实现依赖管理 | - |
| T5.4 | 实现错误恢复机制 | - |
| T5.5 | 与现有自动化引擎集成 | - |
| T5.6 | 端到端测试 | - |

#### Phase 6: 前端集成与测试 (第15-16周)

| 任务 | 说明 | 负责人 |
|-----|------|-------|
| T6.1 | 页面集成与样式优化 | - |
| T6.2 | 用户体验优化 | - |
| T6.3 | 性能优化 | - |
| T6.4 | 安全审计 | - |
| T6.5 | 完整功能测试 | - |
| T6.6 | 文档编写 | - |

---

## 八、技术要点

### 8.1 LLM调用封装

```python
# backend/app/services/llm/llm_client.py

from typing import Optional, Dict, Any
from rag.llm import ChatModel

class LLMClientFactory:
    """LLM客户端工厂 - 复用rag.llm模块"""
    
    @staticmethod
    def get_client(
        factory: str, 
        api_key: str, 
        model_name: str,
        base_url: Optional[str] = None
    ) -> Any:
        """获取LLM客户端"""
        assert factory in ChatModel, f"Chat model from {factory} is not supported yet."
        return ChatModel[factory](
            key=api_key,
            model_name=model_name,
            base_url=base_url
        )
    
    @staticmethod
    async def chat(
        client: Any, 
        messages: list,
        **kwargs
    ) -> str:
        """对话接口"""
        message, token_count = await client.async_chat(None, messages, kwargs)
        return message
```

### 8.2 提示词管理

```python
# backend/app/services/llm/prompt_manager.py

from typing import Dict
import json

class PromptManager:
    """提示词管理器"""
    
    DEFAULT_PROMPTS = {
        "intent_classification": "你是一个意图分类专家...",
        "parameter_extraction": "你是一个化工参数提取专家...",
        "translation_professional": "你是一个专业的化工领域翻译专家...",
        "translation_technical": "你是一个技术文档翻译专家...",
        "report_generation": "你是一个化工技术文档专家...",
        "parameter_mapping": "你是一个化工软件参数映射专家..."
    }
    
    @classmethod
    def get_prompt(cls, key: str, **kwargs) -> str:
        """获取提示词"""
        template = cls.DEFAULT_PROMPTS.get(key, "")
        return template.format(**kwargs) if kwargs else template
    
    @classmethod
    def update_prompt(cls, key: str, template: str):
        """更新提示词"""
        cls.DEFAULT_PROMPTS[key] = template
```

### 8.3 缓存策略

```python
# backend/app/services/cache/ translation_cache.py

from typing import Optional
import hashlib
import json
from datetime import timedelta

class TranslationCache:
    """翻译缓存"""
    
    def __init__(self, redis_client=None):
        self.memory_cache = {}
        self.redis = redis_client
        
    def get(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """获取缓存"""
        key = self._make_key(text, source_lang, target_lang)
        
        # 先查Redis
        if self.redis:
            cached = self.redis.get(key)
            if cached:
                return cached
                
        # 再查内存
        if key in self.memory_cache:
            return self.memory_cache[key]["content"]
            
        return None
    
    def set(self, text: str, source_lang: str, target_lang: str, translation: str, ttl: int = 86400):
        """设置缓存"""
        key = self._make_key(text, source_lang, target_lang)
        
        # 存Redis
        if self.redis:
            self.redis.setex(key, ttl, translation)
            
        # 存内存
        self.memory_cache[key] = {
            "content": translation,
            "expire_at": datetime.now() + timedelta(seconds=ttl)
        }
    
    def _make_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """生成缓存键"""
        content = f"{text[:100]}:{source_lang}:{target_lang}"
        return f"trans:{hashlib.md5(content.encode()).hexdigest()}"
```

---

## 九、配置文件

### 9.1 环境变量

```bash
# .env

# LLM配置 (复用现有)
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx

# 翻译服务配置
TRANSLATION_CACHE_ENABLED=true
TRANSLATION_CACHE_TTL=86400
TRANSLATION_DEFAULT_STYLE=professional

# 报告服务配置
REPORT_OUTPUT_DIR=./reports
REPORT_DEFAULT_FORMAT=pdf

# Agent服务配置
AGENT_MAX_RETRIES=3
AGENT_TASK_TIMEOUT=300

# 工具编排配置
ORCHESTRATOR_MAX_PARALLEL=3
ORCHESTRATOR_STEP_TIMEOUT=60
```

### 9.2 数据库扩展

```sql
-- 扩展tenant_llm表

ALTER TABLE tenant_llm 
ADD COLUMN usage_types TEXT DEFAULT '["chat"]',
ADD COLUMN translation_prompt TEXT,
ADD COLUMN report_prompt TEXT;

-- 翻译缓存表
CREATE TABLE translation_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key TEXT UNIQUE NOT NULL,
    source_text TEXT NOT NULL,
    translated_text TEXT NOT NULL,
    source_lang VARCHAR(10),
    target_lang VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expire_at TIMESTAMP
);

-- Agent任务表
CREATE TABLE agent_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id VARCHAR(50) UNIQUE NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    intent VARCHAR(50),
    input_text TEXT,
    parameters TEXT,
    execution_plan TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 十、测试计划

### 10.1 单元测试

| 模块 | 测试项 | 预期结果 |
|-----|-------|---------|
| AgentService | 意图识别准确率 | >90% |
| AgentService | 参数提取完整性 | >85% |
| TranslationService | 翻译准确率(专业术语) | >90% |
| TranslationService | 缓存命中率 | >60% |
| ReportService | 报告生成正确性 | 100% |
| ToolOrchestrator | 依赖解析正确性 | 100% |

### 10.2 集成测试

| 场景 | 测试步骤 | 验收标准 |
|-----|--------|---------|
| 端到端翻译 | 上传PDF → 解析 → 翻译 → 输出 | 翻译结果正确 |
| 端到端报告 | 解析文档 → 提取数据 → 生成报告 | 报告格式正确 |
| Agent任务 | 输入自然语言 → 意图识别 → 执行 → 返回结果 | 执行结果正确 |

---

## 十一、风险与对策

| 风险 | 影响 | 对策 |
|-----|-----|-----|
| LLM API调用失败 | 功能不可用 | 添加降级机制，使用备选LLM |
| 翻译质量不稳定 | 用户体验差 | 提供多LLM选择，允许用户调整提示词 |
| 长文本处理超时 | 大文档无法处理 | 分段处理，增加进度提示 |
| 并发过高 | 系统负载大 | 添加请求队列，限制并发数 |

---

## 十二、总结

本方案通过复用 `llm_app.py` 的LLM配置体系，结合 `项目架构设计.md` 中的Agent Orchestration Layer架构，形成了一套完整的项目升级执行方案。核心优势包括：

1. **用户友好**：用户只需配置一次LLM，即可用于翻译、报告生成、Agent任务
2. **成本优化**：复用现有LLM资源，无需额外付费
3. **质量可控**：通过精心设计的Prompt保证输出质量
4. **易于扩展**：模块化设计，便于后续添加新功能

方案实施后，Aifiller将具备：
- 智能文档翻译功能（支持多语言、专业术语）
- 自动报告生成功能（多种模板、多格式输出）
- LLM驱动的自动化任务处理能力（意图识别、参数提取、工作流编排）


升级开发的第一阶段已经完成！以下是已创建的核心模块：

## 已完成的后端服务
### 1. LLM服务层 (backend/app/services/llm/)
文件 功能 llm_client.py LLM客户端封装，支持OpenAI、Claude、Ollama prompt_manager.py 提示词管理模板

### 2. Agent服务层 (backend/app/services/agent/)
文件 功能 agent_service.py 智能代理服务：意图识别、参数提取、执行计划生成

### 3. 翻译服务层 (backend/app/services/translation/)
文件 功能 llm_translation_service.py 基于LLM的翻译服务，支持文档翻译和缓存

### 4. 报告服务层 (backend/app/services/report/)
文件 功能 llm_report_generator.py 基于LLM的报告生成，支持多种报告类型

### 5. 工具编排层 (backend/app/services/orchestration/)
文件 功能 tool_orchestrator.py 工具编排器，协调多服务完成任务

### 6. API路由层 (backend/app/routes/)
文件 功能 agent.py Agent API translation.py 翻译 API report.py 报告 API

## 新增API端点
- POST /api/agent/process - 处理用户请求
- GET /api/agent/intents - 获取支持的意图类型
- POST /api/agent/execute_plan - 执行生成的计划
- POST /api/translation/translate - 翻译文本
- POST /api/translation/document - 翻译文档
- POST /api/report/generate - 生成报告
- POST /api/report/parameter_summary - 生成参数汇总报告
- POST /api/report/comparison - 生成对比报告

升级开发已完成！让我总结一下已创建的所有内容：

## 后端服务 (Phase 1-5 完成)
目录 文件 功能 backend/app/services/llm/ llm_client.py LLM客户端封装 (OpenAI/Claude/Ollama) prompt_manager.py 提示词管理模板 backend/app/services/agent/ agent_service.py Agent核心服务 (意图识别、参数提取) backend/app/services/translation/ llm_translation_service.py LLM翻译服务 backend/app/services/report/ llm_report_generator.py LLM报告生成 backend/app/services/orchestration/ tool_orchestrator.py 工具编排器 backend/app/routes/ agent.py Agent API translation.py 翻译 API report.py 报告 API

## 前端页面 (Phase 6 完成)
文件 功能 frontend/src/pages/AgentPanel.tsx 智能Agent控制面板 frontend/src/pages/TranslationPanel.tsx 文档翻译页面 frontend/src/pages/ReportPanel.tsx 报告生成页面 frontend/src/services/agentApi.ts API服务封装

## 新增功能
### API端点
- POST /api/agent/process - 处理智能请求
- POST /api/agent/execute_plan - 执行任务计划
- POST /api/translation/translate - 翻译文本
- POST /api/translation/document - 翻译文档
- POST /api/report/generate - 生成报告
### 前端导航
- 智能Agent - /agent
- 文档翻译 - /translation
- 报告生成 - /report
### 配置方式
系统使用环境变量配置LLM：

```
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
OLLAMA_BASE_URL=http://localhost:11434
```
## 后续优化建议
1. 与现有llm_app.py深度集成，共享用户配置
2. 添加数据库持久化（翻译缓存、任务历史）
3. 完善PDF/Word文档翻译功能
4. 添加更多报告模板
5. 集成Aspen Plus/DWSIM模拟
升级开发的核心框架已完成