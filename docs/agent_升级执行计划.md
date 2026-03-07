# UnveilChem Agent 智能化升级执行计划

## 一、项目背景与目标

### 1.1 项目现状
UnveilChem 当前定位为"智能化工文档分析平台"，已具备以下核心能力：
- 文档/图片解析与参数提取
- LLM 配置管理（支持多厂商）
- 自动化任务调度系统
- 软件适配器架构（Excel、DWSIM、Aspen Plus、AutoCAD 等）

### 1.2 升级目标
将项目升级为**"智能化自动化化工软件操作平台"**，实现：
- 软件自动发现与识别
- 自然语言任务理解与分解
- 自动化软件操作执行
- 结果智能解析与报告生成

### 1.3 参考架构
参考 OpenClaw 的"Gateway + Skill + Node"五层架构：
```
┌─────────────────────────────────────────┐
│           Gateway (网关层)              │
├─────────────────────────────────────────┤
│           Skill (技能层)                │
├─────────────────────────────────────────┤
│           Node (节点层)                 │
├─────────────────────────────────────────┤
│         Observer (观察层)               │
├─────────────────────────────────────────┤
│            LLM (大模型层)               │
└─────────────────────────────────────────┘
```

---

## 二、现有代码架构分析

### 2.1 后端目录结构
```
backend/app/
├── routes/
│   ├── automation.py          # 自动化API路由 ✅ 已实现
│   └── llm_config.py           # LLM配置路由 ✅ 已实现
├── services/
│   ├── automation/
│   │   ├── automation_engine.py    # 自动化引擎 ✅ 已实现
│   │   ├── base_adapter.py         # 适配器基类 ✅ 已实现
│   │   ├── aspen_plus.py           # Aspen Plus适配器 ✅ 已实现
│   │   ├── dwsim_adapter.py        # DWSIM适配器 ✅ 已实现
│   │   ├── excel_adapter.py        # Excel适配器 ✅ 已实现
│   │   ├── autocad_adapter.py      # AutoCAD适配器 ✅ 已实现
│   │   ├── parameter_mapper.py     # 参数映射器 ✅ 已实现
│   │   ├── scheduler.py            # 任务调度器 ✅ 已实现
│   │   └── error_handler.py        # 错误处理器 ✅ 已实现
│   └── llm/
│       └── llm_config_service.py   # LLM配置服务 ✅ 已实现
└── models/
    └── llm_config.py           # LLM配置模型 ✅ 已实现
```

### 2.2 已有的能力映射
| OpenClaw 概念 | 现有实现 | 状态 |
|---------------|---------|------|
| Node (节点) | SoftwareAutomationAdapter | ✅ 已实现 |
| Skill (技能) | Adapter 注册机制 | ⚠️ 需标准化 |
| 任务调度 | AutomationEngine | ✅ 已实现 |
| 错误处理 | ErrorHandler | ✅ 已实现 |
| LLM 层 | LLMConfig 模块 | ✅ 已实现 |

### 2.3 缺失的关键功能
| 功能 | 优先级 | 状态 |
|------|--------|------|
| 软件自动发现 | P0 | ❌ 未实现 |
| Skill 标准化封装 | P0 | ❌ 未实现 |
| LLM 任务理解 | P1 | ❌ 未实现 |
| Think-Act-Observe 循环 | P1 | ❌ 未实现 |

---

## 三、升级执行计划

### 3.1 阶段一：软件自动发现 (Software Discovery)

#### 目标
实现本地安装化工软件的自动扫描与识别

#### 实施方案
```python
# 新增文件: backend/app/services/automation/software_discovery.py
class SoftwareDiscovery:
    """软件自动发现服务"""

    # 已知软件安装路径
    SOFTWARE_PATHS = {
        "dwsim": [
            r"C:\Program Files\DWSIM\DWSIM.exe",
            r"C:\Program Files (x86)\DWSIM\DWSIM.exe"
        ],
        "aspen_plus": [
            r"C:\Program Files\AspenTech\Aspen Plus V14.2\xxe.exe",
            r"C:\Program Files\AspenTech\Aspen Plus V12.1\xxe.exe"
        ],
        "excel": [
            r"C:\Program Files\Microsoft Office\root\Office*\EXCEL.EXE"
        ],
        "autocad": [
            r"C:\Program Files\Autodesk\AutoCAD *\acad.exe"
        ]
    }

    def scan_installed_software(self) -> List[DetectedSoftware]:
        """扫描本地安装的软件"""
        pass

    def check_software_status(self, software_name: str) -> SoftwareStatus:
        """检查软件运行状态"""
        pass
```

#### 工作任务
| 序号 | 任务 | 文件 | 预估工作量 |
|------|------|------|-----------|
| 1.1 | 创建 SoftwareDiscovery 类 | software_discovery.py | 4h |
| 1.2 | 实现注册表扫描 | software_discovery.py | 2h |
| 1.3 | 实现路径扫描 | software_discovery.py | 2h |
| 1.4 | 添加软件状态检测 | software_discovery.py | 2h |
| 1.5 | 创建 API 端点 | automation.py | 1h |

#### 交付物
- `backend/app/services/automation/software_discovery.py`
- `GET /api/automation/discover-software` 端点

---

### 3.2 阶段二：Skill 标准化封装

#### 目标
将现有适配器封装为标准化的 Skill 结构，支持关键词自动激活

#### 实施方案
```python
# 新增文件: backend/app/services/automation/skill.py
class Skill(BaseModel):
    """Skill 标准化模型"""
    name: str                          # 技能标识
    display_name: str                  # 显示名称
    keywords: List[str]               # 激活关键词
    description: str                  # 能力描述
    software_type: str                # 依赖软件类型
    actions: List[SkillAction]        # 支持的操作
    parameters: Dict[str, Any]       # 参数定义

class SkillAction(BaseModel):
    """Skill 操作定义"""
    name: str                          # 操作名称
    description: str                  # 操作描述
    required_params: List[str]        # 必需参数
    optional_params: List[str]        # 可选参数
```

#### 现有适配器改造
| 适配器 | 需添加字段 |
|--------|-----------|
| AspenPlusAdapter | keywords, actions |
| DWSIMAdapter | keywords, actions |
| ExcelAdapter | keywords, actions |
| AutoCADAdapter | keywords, actions |

#### 工作任务
| 序号 | 任务 | 文件 | 预估工作量 |
|------|------|------|-----------|
| 2.1 | 创建 Skill 数据模型 | skill.py | 2h |
| 2.2 | 定义 Skill 注册表 | skill_registry.py | 2h |
| 2.3 | 改造 AspenPlusAdapter | aspen_plus.py | 1h |
| 2.4 | 改造 DWSIMAdapter | dwsim_adapter.py | 1h |
| 2.5 | 改造 ExcelAdapter | excel_adapter.py | 1h |
| 2.6 | 改造 AutoCADAdapter | autocad_adapter.py | 1h |
| 2.7 | 实现关键词匹配引擎 | skill_matcher.py | 3h |
| 2.8 | 添加 Skill 查询 API | automation.py | 1h |

#### 交付物
- `backend/app/services/automation/skill.py`
- `backend/app/services/automation/skill_registry.py`
- `backend/app/services/automation/skill_matcher.py`
- `GET /api/automation/skills` 端点

---

### 3.3 阶段三：LLM 任务理解

#### 目标
利用 LLM 理解用户的自然语言需求，自动规划执行步骤

#### 实施方案
```python
# 新增文件: backend/app/services/automation/task_understanding.py
class TaskUnderstandingService:
    """任务理解服务"""

    def understand_user_request(
        self,
        user_request: str,
        available_skills: List[Skill]
    ) -> ExecutionPlan:
        """
        理解用户请求，生成执行计划

        Args:
            user_request: 用户自然语言请求
            available_skills: 可用的 Skills 列表

        Returns:
            ExecutionPlan: 包含步骤的执行计划
        """
        pass

class ExecutionPlan(BaseModel):
    """执行计划"""
    task_id: str
    original_request: str
    steps: List[ExecutionStep]
    estimated_time: float
    confidence: float

class ExecutionStep(BaseModel):
    """执行步骤"""
    step_id: int
    skill_name: str
    action: str
    parameters: Dict[str, Any]
    depends_on: List[int]
```

#### Prompt 设计
```python
TASK_UNDERSTANDING_PROMPT = """
你是一个化工软件自动化助手。用户会用自然语言描述想要执行的任务。

可用技能：
{skills_list}

请分析用户请求，生成执行步骤。

用户请求：{user_request}

请按以下 JSON 格式返回：
{{
    "task_type": "任务类型",
    "required_skills": ["需要的技能"],
    "steps": [
        {{
            "step_id": 1,
            "skill": "技能名称",
            "action": "操作名称",
            "parameters": {{参数}}
        }}
    ],
    "confidence": 0.95
}}
"""
```

#### 工作任务
| 序号 | 任务 | 文件 | 预估工作量 |
|------|------|------|-----------|
| 3.1 | 创建 TaskUnderstandingService | task_understanding.py | 4h |
| 3.2 | 设计任务理解 Prompt | task_understanding.py | 2h |
| 3.3 | 实现执行计划生成 | task_understanding.py | 3h |
| 3.4 | 添加任务理解 API | automation.py | 1h |
| 3.5 | 与 LLM 配置集成 | llm_config_service.py | 2h |

#### 交付物
- `backend/app/services/automation/task_understanding.py`
- `POST /api/automation/understand-task` 端点

---

### 3.4 阶段四：Think-Act-Observe 循环

#### 目标
实现智能体执行机制，支持思考、执行、观察的迭代循环

#### 实施方案
```python
# 新增文件: backend/app/services/automation/agent_engine.py
class化工Agent:
    """化工软件自动化智能体"""

    async def execute(
        self,
        user_request: str,
        max_iterations: int = 10
    ) -> AgentResult:
        """
        执行智能体循环

        循环过程：
        1. Think: 理解当前状态，规划下一步
        2. Act: 执行操作
        3. Observe: 观察结果，评估是否需要重试
        """
        pass

    async def think(self, context: AgentContext) -> PlanStep:
        """思考阶段：分析状态，决定下一步"""
        pass

    async def act(self, step: PlanStep) -> ActionResult:
        """执行阶段：执行计划步骤"""
        pass

    async def observe(self, result: ActionResult) -> Observation:
        """观察阶段：评估执行结果"""
        pass
```

#### 工作任务
| 序号 | 任务 | 文件 | 预估工作量 |
|------|------|------|-----------|
| 4.1 | 创建 AgentEngine 类 | agent_engine.py | 4h |
| 4.2 | 实现 Think 逻辑 | agent_engine.py | 3h |
| 4.3 | 实现 Act 逻辑 | agent_engine.py | 3h |
| 4.4 | 实现 Observe 逻辑 | agent_engine.py | 3h |
| 4.5 | 实现循环控制 | agent_engine.py | 2h |
| 4.6 | 添加智能体执行 API | automation.py | 1h |
| 4.7 | 添加结果解析服务 | result_parser.py | 3h |

#### 交付物
- `backend/app/services/automation/agent_engine.py`
- `backend/app/services/automation/result_parser.py`
- `POST /api/automation/execute-agent` 端点

---

## 四、前端改造计划

### 4.1 智能Agent页面升级
```typescript
// 改造文件: frontend/src/pages/AgentPanel.tsx

// 新增功能：
// 1. 自然语言输入框
// 2. 执行计划可视化展示
// 3. 实时执行状态
// 4. 结果展示与导出
```

### 4.2 软件发现页面
```typescript
// 新增文件: frontend/src/pages/SoftwareDiscovery.tsx

// 功能：
// 1. 显示已发现软件列表
// 2. 软件状态指示
// 3. 一键注册适配器
```

### 4.3 Skill 管理页面
```typescript
// 新增/改造: frontend/src/pages/SkillManagement.tsx

// 功能：
// 1. Skill 列表展示
// 2. 关键词配置
// 3. 启用/禁用 Skill
```

---

## 五、API 端点规划

### 5.1 新增端点
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/automation/discover-software | 扫描本地软件 |
| GET | /api/automation/skills | 获取可用 Skills |
| POST | /api/automation/understand-task | 理解任务请求 |
| POST | /api/automation/execute-agent | 执行智能体任务 |
| GET | /api/automation/agent-status/{task_id} | 获取执行状态 |
| GET | /api/automation/agent-result/{task_id} | 获取执行结果 |

### 5.2 改造端点
| 方法 | 路径 | 改造内容 |
|------|------|---------|
| GET | /api/automation/available-adapters | 返回 Skill 格式数据 |

---

## 六、数据库模型变更

### 6.1 新增表
```sql
-- Skill 注册表
CREATE TABLE automation_skills (
    id INT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    display_name VARCHAR(100),
    keywords JSON,
    description TEXT,
    adapter_type VARCHAR(50),
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Agent 执行记录表
CREATE TABLE agent_executions (
    id INT PRIMARY KEY,
    task_id VARCHAR(50),
    user_request TEXT,
    execution_plan JSON,
    status VARCHAR(20),
    result JSON,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Agent 记忆系统表
-- 会话记忆表
CREATE TABLE agent_sessions (
    id INT PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    user_id INT,
    messages JSON,                    -- 对话历史
    current_plan JSON,                -- 当前执行计划
    context JSON,                     -- 上下文信息
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 执行记忆表 - 历史任务记录
CREATE TABLE agent_execution_history (
    id INT PRIMARY KEY,
    session_id VARCHAR(50),
    task_request TEXT,               -- 任务请求
    execution_plan JSON,              -- 执行计划
    steps JSON,                       -- 执行的步骤及结果
    status VARCHAR(20),               -- 执行状态
    result JSON,                      -- 最终结果
    error_message TEXT,               -- 错误信息（如有）
    execution_time FLOAT,             -- 执行耗时（秒）
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- 知识记忆表 - 软件操作知识
CREATE TABLE knowledge_chunks (
    id INT PRIMARY KEY,
    source_type VARCHAR(20),           -- 来源类型: manual, api_spec, best_practice
    source_name VARCHAR(100),         -- 来源名称
    chunk_content TEXT,               -- 分块内容
    embedding VECTOR(1536),            -- 向量嵌入 (可选)
    keywords JSON,                    -- 关键词
    metadata JSON,                    -- 元数据
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 记忆索引表 - 用于快速检索
CREATE TABLE memory_index (
    id INT PRIMARY KEY,
    chunk_id INT,                     -- 关联的知识块
    memory_type VARCHAR(20),          -- memory_type: session, knowledge, execution
    keywords TEXT,                    -- 关键词索引
    ft_index TSVECTOR,                -- 全文搜索索引
    created_at TIMESTAMP
);
```

---

## 七、依赖项

### 7.1 Python 依赖
```txt
# 新增依赖
openai>=1.0.0          # LLM 调用
anthropic>=0.18.0      # Claude 支持
```

### 7.2 前端依赖
```json
// 可能新增
"react-markdown": "^0.7.0",
"react-flow": "^11.0.0"
```

---

## 八、实施顺序与时间估算

### 8.1 推荐实施顺序
```
Phase 1 (软件发现)     ████████████████████  11h
    ↓
Phase 2 (Skill封装)    ████████████████████████████  14h
    ↓
Phase 3 (LLM理解)      ████████████████████████████  14h
    ↓
Phase 3.5 (记忆系统)   █████████████████████████████  19h  ⭐ 核心组件
    ↓
Phase 4 (执行循环)    ████████████████████████████████  19h
    ↓
前端改造              ████████████████████████████  15h
```

### 8.2 总时间估算
| 阶段 | 工作量 |
|------|--------|
| Phase 1 | 约 11 小时 |
| Phase 2 | 约 14 小时 |
| Phase 3 | 约 14 小时 |
| Phase 3.5 (记忆系统) | 约 19 小时 |
| Phase 4 | 约 19 小时 |
| 前端改造 | 约 15 小时 |
| **总计** | **约 92 小时** |

---

## 九、风险与缓解

### 9.1 技术风险
| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| LLM 调用失败 | 中 | 高 | 添加降级策略，使用规则引擎 |
| 软件版本兼容 | 中 | 中 | 版本检测与适配 |
| 执行超时 | 低 | 高 | 超时控制与断点续传 |

### 9.2 业务风险
| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 需求变更 | 中 | 中 | 敏捷迭代 |
| 测试不充分 | 低 | 高 | 自动化测试覆盖 |

---

## 十、里程碑

### M1: 软件自动发现 (Week 1)
- [ ] 完成 SoftwareDiscovery 开发
- [ ] 前端展示已发现软件
- [ ] 一键注册适配器功能

### M2: Skill 标准化 (Week 2)
- [ ] Skill 模型与注册表
- [ ] 关键词匹配引擎
- [ ] Skill 管理界面

### M3: 任务理解 (Week 3)
- [ ] LLM 任务理解服务
- [ ] 执行计划生成
- [ ] 与现有系统集成

### M3.5: Agent 记忆系统 (Week 3-4) ⭐ 核心组件
#### 为什么需要记忆系统？
参考 OpenClaw/Moltbot 的设计，记忆系统是 Agent 避免幻觉、持续准确完成任务的核心：
- **上下文连贯**：多轮对话中保持信息一致性
- **知识复用**：历史执行经验可被复用
- **错误追溯**：执行失败时可回溯分析原因

#### 记忆系统架构
```
┌─────────────────────────────────────────────────────────┐
│                    Agent 记忆系统                         │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐   │
│  │  会话记忆    │  │  知识记忆    │  │  执行记忆     │   │
│  │ (Sessions)  │  │  (Knowledge) │  │  (Execution) │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘   │
│         │                │                  │            │
│         └────────────────┼──────────────────┘            │
│                          ▼                               │
│              ┌───────────────────────┐                   │
│              │    混合搜索引擎        │                   │
│              │  (Vector + Keyword)   │                   │
│              └───────────┬───────────┘                   │
│                          ▼                               │
│              ┌───────────────────────┐                   │
│              │     SQLite Database   │                   │
│              │  + 向量索引 (可选)     │                   │
│              └───────────────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

#### 记忆类型设计
```python
# 1. 会话记忆 - 当前对话上下文
class SessionMemory:
    """会话记忆 - 当前任务的上下文"""
    session_id: str
    messages: List[ChatMessage]
    current_plan: ExecutionPlan
    step_results: List[StepResult]

# 2. 知识记忆 - 软件操作知识库
class KnowledgeMemory:
    """知识记忆 - 可复用的操作知识"""
    software_manuals: List[ManualChunk]    # 软件手册
    api_specs: List[APISpec]                # API规范
    best_practices: List[BestPractice]      # 最佳实践

# 3. 执行记忆 - 历史执行经验
class ExecutionMemory:
    """执行记忆 - 历史成功/失败经验"""
    task_history: List[TaskRecord]          # 任务执行记录
    success_patterns: List[Pattern]         # 成功模式
    failure_patterns: List[Pattern]         # 失败模式
```

#### 关键技术实现

##### 3.5.1 混合搜索 (Hybrid Search)
```python
class HybridSearchEngine:
    """混合搜索：向量 + 关键词"""

    def search(self, query: str, filters: SearchFilters) -> List[SearchResult]:
        # 1. 向量搜索 - 语义理解
        vector_results = self.vector_search(query, top_k=5)

        # 2. 关键词搜索 - 精确匹配
        keyword_results = self.keyword_search(query, top_k=5)

        # 3. 权重融合
        return self.merge_results(
            vector_results,
            keyword_results,
            vector_weight=0.6,
            keyword_weight=0.4
        )
```

##### 3.5.2 增量同步机制
```python
class MemorySync:
    """增量同步 - 利用 mtime 检测变化"""

    def sync_if_needed(self, memory_source: MemorySource):
        # 比较文件 mtime 快速判断是否修改
        # 使用 hash 精确检测内容变化
        # 只重新索引变化的部分
        pass
```

##### 3.5.3 多级缓存
```python
class MemoryCache:
    """三级缓存策略"""
    L1_MEMORY = MapCache()      # 内存缓存 - 进程内快速访问
    L2_SQLITE = SQLiteCache()  # SQLite缓存 - 跨进程共享
    L3_FILE = FileCache()       # 文件系统 - 持久化存储
```

#### 工作任务
| 序号 | 任务 | 文件 | 预估工作量 |
|------|------|------|-----------|
| 3.5.1 | 创建记忆模型 | memory_models.py | 2h |
| 3.5.2 | 实现混合搜索 | memory_search.py | 4h |
| 3.5.3 | 实现会话记忆 | session_memory.py | 3h |
| 3.5.4 | 实现知识记忆 | knowledge_memory.py | 3h |
| 3.5.5 | 实现执行记忆 | execution_memory.py | 3h |
| 3.5.6 | 实现缓存管理 | memory_cache.py | 2h |
| 3.5.7 | 与 Agent 集成 | agent_engine.py | 2h |

#### 交付物
- `backend/app/services/automation/memory/` (新目录)
  - `memory_models.py` - 记忆数据模型
  - `memory_search.py` - 混合搜索引擎
  - `session_memory.py` - 会话记忆
  - `knowledge_memory.py` - 知识记忆
  - `execution_memory.py` - 执行记忆
  - `memory_cache.py` - 缓存管理

---

### M4: 智能执行 (Week 4-5)
- [ ] Think-Act-Observe 循环
- [ ] 结果解析服务
- [ ] 完整流程测试

---

## 附录 A：参考资源

1. OpenClaw 官方仓库: https://github.com/openclaw
2. OpenClaw Skill 开发指南
3. LangChain Agent 模式
4. React Flow 可视化流程图

---

## 附录 B：代码规范

- 所有新增代码遵循现有代码风格
- 添加完整的 JSDoc/Pydantic 文档
- 新增功能需添加单元测试
- API 变更需更新 API 文档

---

**文档版本**: v1.0
**创建日期**: 2026-03-06
**计划周期**: 4-5 周

## 🎯 Moltbot 记忆存储系统设计分析
### 1. 🔍 混合搜索架构 (Hybrid Search)
巧妙之处 ：同时结合向量搜索和关键词搜索

```
// hybrid.ts - 融合两种搜索结果
export function mergeHybridResults(params: {
  vector: HybridVectorResult[];   // 向量相似度
  keyword: HybridKeywordResult[];  // BM25 关键词匹配
  vectorWeight: number;           // 可调权重
  textWeight: number;
})
```
优势 ：

- 向量搜索 ：理解语义 ("如何煮饭" → 找到 "烹饪大米")
- 关键词搜索 ：精确匹配技术术语
- 权重融合 ：可根据场景调整两种搜索的优先级
### 2. 📦 多层缓存策略
```
// manager.ts
const INDEX_CACHE = new Map<string, MemoryIndexManager>
();  // 内存缓存
const EMBEDDING_CACHE_TABLE = 
"embedding_cache";             // SQLite 缓存
private readonly cache: { enabled: boolean; maxEntries?: 
number };
```
三级缓存 ：

层级 存储位置 用途 L1 内存 Map 进程内快速访问 L2 SQLite 跨进程共享 L3 文件系统 持久化存储

### 3. 🔄 增量同步机制
```
// manager.ts - 利用 mtime 检测变化
type SessionFileEntry = {
  path: string;
  mtimeMs: number;      // 修改时间
  size: number;
  hash: string;         // 内容哈希
};
```
智能检测 ：

- 比较文件 mtimeMs 快速判断是否修改
- 使用 hash 精确检测内容变化
- 只重新索引变化的部分，节省资源
### 4. 🧩 向量嵌入的多提供商支持
```
// embeddings.ts
createEmbeddingProvider({
  provider: "openai" | "gemini" | "local";
  model: string;
  apiKey?: string;
});
```
巧妙设计 ：

- 统一的 Provider 接口
- 支持 OpenAI、Gemini、本地模型
- 批量处理 ：支持 OpenAI Batch API，提高吞吐量
- 错误重试 ：指数退避策略
```
const EMBEDDING_RETRY_MAX_ATTEMPTS = 3;
const EMBEDDING_RETRY_BASE_DELAY_MS = 500;
const EMBEDDING_RETRY_MAX_DELAY_MS = 8000;
```
### 5. 📝 智能文本分块 (Chunking)
```
// internal.ts
export function chunkMarkdown(
  content: string,
  chunking: { tokens: number; overlap: number }
): MemoryChunk[]
```
策略 ：

- Token 估算 ：1 token ≈ 1 字符（简化计算）
- 重叠窗口 ：相邻 chunk 共享内容，保持上下文连续性
- Markdown 感知 ：按标题、段落自然分割
### 6. 🗄️ SQLite + sqlite-vec 向量引擎
```
// sqlite-vec.ts
import { loadSqliteVecExtension } from "./sqlite-vec.js";

// 向量存储
const VECTOR_TABLE = "chunks_vec";
// 全文搜索
const FTS_TABLE = "chunks_fts";
```
巧妙之处 ：

- 单一 SQLite 数据库，同时支持向量和全文搜索
- sqlite-vec 扩展提供高效向量相似度计算
- 无需部署独立的向量数据库（如 Pinecone、Weaviate）
### 7. 📁 文件系统监视
```
// manager.ts
import chokidar from "chokidar";

private watcher?: FSWatcher;

async startWatcher() {
  this.watcher = chokidar.watch(watchPaths, {
    persistent: true,
    ignoreInitial: true,
  });
}
```
实时同步 ：

- 监视 memory/ 目录和 MEMORY.md 文件变化
- 自动触发增量索引
- 防抖处理避免频繁更新
### 8. 🎛️ 灵活的配置系统
```
// agents/memory-search.ts
type ResolvedMemorySearchConfig = {
  enabled: boolean;
  provider: "openai" | "gemini" | "local" | "auto";
  model: string;
  chunkTokens: number;
  chunkOverlap: number;
  hybrid?: {
    vectorWeight: number;
    textWeight: number;
  };
};
```
按 Agent 独立配置 ：每个 Agent 可以有不同的记忆搜索配置

### 9. 🛡️ 错误恢复与降级
```
// batch-openai.ts
const BATCH_FAILURE_LIMIT = 2;
// 向量不可用时回退到纯关键词搜索
private fallbackFrom?: "openai" | "local" | "gemini";
```
容错设计 ：

- 向量引擎加载失败 → 纯关键词搜索
- API 调用失败 → 重试 + 降级
- 单个文件索引失败 → 继续处理其他文件
### 10. 🔑 会话记忆集成
```
// manager.ts
type MemorySource = "memory" | "sessions";
private readonly sources: Set<MemorySource>;

// 自动加载会话记录
await onSessionTranscriptUpdate(agentId, callback);
```
统一索引 ：将 Agent 记忆和会话记录放在同一索引中搜索

## 📊 整体架构图
```
┌─────────────────────────────────────────────────────────
┐
│                    
MemoryIndexManager                    │
├─────────────────────────────────────────────────────────
┤
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │  Memory.md  │  │  memory/    │  │  Sessions    │  │
│  │   文件      │  │   目录      │  │   记录       │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘  │
│         │                │                  │           
│
│         └────────────────┼──────────────────┘           
│
│                          ▼                              
│
│              
┌───────────────────────┐                   │
│              │   Chokidar Watcher   │                   
│
│              
└───────────┬───────────┘                   │
│                          ▼                              
│
│              
┌───────────────────────┐                   │
│              │  buildFileEntry()     
│                   │
│              │  chunkMarkdown()      
│                   │
│              
└───────────┬───────────┘                   │
│                          ▼                              
│
│     ┌────────────────────────────────────────────┐      
│
│     │           嵌入生成 (Embedding)              │      
│
│     │  ┌─────────┐  ┌─────────┐  ┌───────────┐  │      │
│     │  │ OpenAI  │  │ Gemini  │  │  Local    │  │      │
│     │  │ Batch   │  │ Batch   │  │  (本地)   │  │      │
│     │  └────┬────┘  └────┬────┘  └─────┬─────┘  │      │
│     
└───────┼─────────────┼──────────────┼────────┘      │
│             │             │              
│                │
│             
└─────────────┼──────────────┘                │
│                           
▼                              │
│     ┌────────────────────────────────────────────┐      
│
│     │              SQLite Database                
│      │
│     │  ┌─────────────┐    ┌─────────────────┐  │      │
│     │  │ chunks_vec  │    │   chunks_fts     │  │      │
│     │  │ (向量索引)  │    │  (全文搜索索引)  │  │      │
│     │  └─────────────┘    └─────────────────┘  │      │
│     │  ┌─────────────────────────────────────┐  │      │
│     │  │       embedding_cache (嵌入缓存)    │  │      │
│     │  └─────────────────────────────────────┘  │      │
│     └────────────────────────────────────────────┘      
│
│                           
│                              │
│                           
▼                              │
│     ┌────────────────────────────────────────────┐      
│
│     │          混合搜索 (Hybrid Search)          │      │
│     │  ┌─────────────────┐  ┌────────────────┐  │      │
│     │  │ Vector Search   │  │ Keyword Search │  │      │
│     │  │ (向量相似度)    │  │   (BM25)       │  │      │
│     │  └────────┬────────┘  └───────┬────────┘  │      │
│     │           │                    │           │      
│
│     │           └─────────┬──────────┘           │      
│
│     │                     ▼                      │      
│
│     │           mergeHybridResults()             │      
│
│     │           (权重融合结果)                   │      │
│     └─────────────────────┬─────────────────────┘      │
│                           
│                              │
│                           
▼                              │
│              
┌───────────────────────┐                    │
│              │  MemorySearchResult  
│                    │
│              │  (最终搜索结果)      │                    
│
│              
└───────────────────────┘                    │
└─────────────────────────────────────────────────────────
┘
```
## 🎓 设计哲学总结
原则 实现方式 单一职责 向量存储、关键词存储、缓存分离 开放/封闭 通过 Provider 接口支持新模型 依赖注入 配置驱动的嵌入提供商 延迟加载 按需加载 sqlite-vec 扩展 缓存为王 多级缓存减少 API 调用 容错优先 优雅降级保证服务可用

这个系统展示了如何在资源受限的环境中构建企业级的记忆搜索能力，巧妙地平衡了功能、性能和成本。

## Phase 1 完成情况
我已完成 软件自动发现 功能的开发：

### 1. 新增文件
- backend/app/services/automation/software_discovery.py - 软件发现服务
### 2. 新增 API 端点
方法 路径 功能 GET /api/automation/discover-software 扫描本地软件 GET /api/automation/software-status/{software_name} 检查特定软件状态 POST /api/automation/register-discovered-software/{software_name} 注册已发现软件

### 3. 支持扫描的软件
- DWSIM (化工流程模拟)
- Aspen Plus (化工流程模拟)
- Excel (办公软件)
- AutoCAD (CAD软件)
- PRO/II (化工流程模拟)
- ChemCAD (化工流程模拟)
- Aspen HYSYS (过程模拟)
- SolidWorks (3D CAD)
## 下一步
Phase 1 已完成 ，你可以在浏览器中访问：

- http://localhost:8000/api/automation/discover-software
查看返回的 JSON 数据，应该会显示已扫描到的软件列表。

### Phase 2: Skill 标准化封装 ✅
- 新增文件 : skill.py
- 包含 6 个预定义 Skills :
  
  - DWSIM (化工流程模拟)
  - Aspen Plus (化工流程模拟)
  - Excel (办公软件)
  - AutoCAD (CAD设计)
  - PRO/II (化工流程模拟)
  - ChemCAD (化工流程模拟)
- API 端点 :
  
  方法 路径 功能 GET /api/automation/skills 获取所有 Skills GET /api/automation/skills/{skill_name} 获取 Skill 详情 GET /api/automation/skills/search/{keyword} 关键词搜索 Skills POST /api/automation/skills/{skill_name}/toggle 启用/禁用 Skill

### 新增 API 端点汇总 Phase 1 - 软件发现
方法 路径 功能 GET /api/automation/discover-software 扫描本地软件 GET /api/automation/software-status/{name} 检查软件状态 POST /api/automation/register-discovered-software/{name} 注册软件
 Phase 2 - Skill 管理
方法 路径 功能 GET /api/automation/skills 获取所有 Skills GET /api/automation/skills/{name} 获取 Skill 详情 GET /api/automation/skills/search/{keyword} 关键词搜索 POST /api/automation/skills/{name}/toggle 启用/禁用
 Phase 3 - 任务理解
方法 路径 功能 POST /api/automation/understand-task 理解任务请求 POST /api/automation/validate-plan 验证执行计划 GET /api/automation/task-types 获取任务类型

Phase 3.5 - Agent 记忆系统
方法 路径 功能 POST /api/automation/memory/session 创建新会话 GET /api/automation/memory/session/{id} 获取会话详情 POST /api/automation/memory/session/{id}/message 添加消息 POST /api/automation/memory/knowledge 添加知识 GET /api/automation/memory/knowledge/search 搜索知识库 GET /api/automation/memory/search 统一搜索 GET /api/automation/memory/stats 获取统计

### 记忆系统核心功能
1. 会话记忆 - 维护对话上下文
2. 知识记忆 - 存储软件操作知识（预置 DWSIM、Aspen、Excel 等手册）
3. 执行记忆 - 记录历史执行经验，支持相似任务推荐
4. 混合搜索 - 关键词 + 语义搜索

## ✅ Phase 4 完成内容
### 新增文件
- agent_engine.py - Agent执行引擎
### 新增API端点
方法 路径 功能 POST /api/automation/agent/execute 执行Agent任务 GET /api/automation/agent/status/{session_id} 获取执行状态 GET /api/automation/agent/active 列出活跃Agent GET /api/automation/agent/executions 获取执行历史 GET /api/automation/agent/execution/{record_id} 获取执行详情

### Agent执行流程
```
Think → 理解任务，生成执行计划
  ↓
Act → 执行当前步骤
  ↓
Observe → 观察结果，评估是否成功
  ↓
循环 → 执行下一个步骤或结束
```
## 📊 所有阶段完成情况
阶段 状态 完成时间 Phase 1: 软件自动发现 ✅ 完成 之前 Phase 2: Skill标准化封装 ✅ 完成 之前 Phase 3: LLM任务理解 ✅ 完成 之前 Phase 3.5: Agent记忆系统 ✅ 完成 之前 Phase 4: Think-Act-Observe ✅ 完成 本次

所有后端核心功能已完成开发！现在系统具备：

1. 软件自动发现 - 自动扫描本地化工软件
2. Skill标准化 - 6个预定义Skills，关键词激活
3. 任务理解 - 自然语言转执行计划
4. 记忆系统 - 会话/知识/执行记忆，混合搜索
5. Agent执行 - Think-Act-Observe循环

## ✅ 后端服务验证完成！
后端已在端口 8001 成功启动并运行

### 测试结果汇总
API 状态 说明 Skills API ✅ 通过 返回6个Skills 任务理解 API ✅ 通过 正确识别任务类型和所需Skills 记忆系统 API ✅ 通过 会话创建、知识搜索正常 Agent执行 API ✅ 通过 Think-Act-Observe循环执行成功

### Agent执行示例
- 请求 : "打开Excel文件并读取数据"
- 执行时间 : 0.51秒
- 结果 : 成功 ✅
### 可访问的API端点
- http://localhost:8001/api/automation/skills
- http://localhost:8001/api/automation/understand-task
- http://localhost:8001/api/automation/agent/execute
- http://localhost:8001/api/automation/memory/session
- http://localhost:8001/api/automation/discover-software
所有5个阶段的后端功能已完成开发并验证通过！

## ✅ 前端对接完成！
### 已完成的修改 1. 修改 AgentPanel.tsx
- 新增Tab页面 ：
  - 智能对话 (Tab 1) - 保留原有功能
  - 化工自动化 (Tab 2) - 新增Agent执行功能
    - 执行任务按钮
    - 理解任务按钮
    - 快速示例标签
    - 执行结果展示（状态、步骤详情、Timeline）
    - 可用Skills卡片展示
  - 执行历史 (Tab 3) - 查看历史执行记录
  - 记忆系统 (Tab 4) - 查看记忆统计 2. 新建 agentAutomation.ts
包含所有新API的封装：

- 软件发现
- Skills管理
- 任务理解
- Agent执行
- 记忆系统
### 前端功能预览
功能 位置 说明 化工软件操作 AgentPanel Tab 2 自然语言控制化工软件 Skills展示 AgentPanel Tab 2 显示6个预定义Skills 执行历史 AgentPanel Tab 3 查看历史任务 记忆统计 AgentPanel Tab 4 查看会话/知识/执行记忆

### 访问方式
在浏览器中访问： http://localhost:5173/agent

所有功能已集成到现有的"智能Agent"菜单中，无需新增导航入口。



DWSIM COM 接口可以加载！ 虽然有一个警告，但核心功能可用。

关键方法：

- CalculateFlowsheet2 - 运行仿真
- CreateFlowsheet - 创建流程
- LoadFlowsheet - 加载流程
- SaveFlowsheet - 保存流程
- AvailableCompounds - 获取可用化合物
- AvailablePropertyPackages - 获取物性包