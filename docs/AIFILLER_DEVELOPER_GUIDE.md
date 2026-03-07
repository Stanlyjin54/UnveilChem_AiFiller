# Aifiller 开发者文档

## 1. 项目概述

### 1.1 项目简介
Aifiller 是一款化学文档参数提取工具，采用前后端分离架构，后端基于 FastAPI，前端基于 React，支持多种文档格式的解析和参数提取。

### 1.2 技术栈

#### 后端
- **框架**: FastAPI
- **ORM**: SQLAlchemy
- **数据库**: SQLite/MySQL
- **认证**: JWT
- **解析器**: PyMuPDF、Tesseract、Pix2Text、PaddleOCR

#### 前端
- **框架**: React
- **构建工具**: Vite
- **状态管理**: Context API
- **UI组件**: Ant Design
- **HTTP客户端**: Axios

#### 解析器模块
- **统一解析器**: `parsers/unified_parser.py`
- **PDF解析**: `parsers/pymupdf_parser.py`
- **表格解析**: `parsers/camelot_parser.py`
- **OCR识别**: `parsers/tesseract_parser.py`
- **多格式解析**: `parsers/tika_parser.py`

## 2. 项目结构

### 2.1 目录结构
```
UnveilChem_AiFiller/
├── backend/                    # 后端代码
│   ├── app/                    # 应用代码
│   │   ├── config/             # 配置文件
│   │   ├── models/             # 数据库模型
│   │   ├── routes/             # API路由
│   │   ├── schemas/            # 数据模型
│   │   ├── services/           # 业务逻辑
│   │   │   ├── document_parsers/  # 文档解析器
│   │   │   └── ...             # 其他服务
│   │   ├── utils/              # 工具函数
│   │   ├── database.py         # 数据库配置
│   │   └── main.py             # 应用入口
│   ├── requirements.txt        # 依赖列表
│   └── ...                     # 其他配置文件
├── frontend/                   # 前端代码
│   ├── src/                    # 源代码
│   │   ├── components/         # 组件
│   │   ├── contexts/           # 上下文
│   │   ├── hooks/              # 自定义钩子
│   │   ├── pages/              # 页面
│   │   ├── services/           # API服务
│   │   ├── utils/              # 工具函数
│   │   ├── App.jsx             # 应用组件
│   │   └── main.jsx            # 入口文件
│   ├── package.json            # 依赖配置
│   └── ...                     # 其他配置文件
├── parsers/                    # 解析器模块
│   ├── __init__.py             # 模块初始化
│   ├── camelot_parser.py       # 表格解析器
│   ├── pymupdf_parser.py       # PDF解析器
│   ├── tesseract_parser.py     # OCR解析器
│   ├── tika_parser.py          # 多格式解析器
│   └── unified_parser.py       # 统一解析器
├── AIFILLER_UPGRADE_PLAN.md    # 升级执行方案
├── AIFILLER_USER_GUIDE.md      # 用户使用说明
├── PARSERS模块说明.md          # 解析器模块说明
└── ...                         # 其他文档
```

## 3. 开发环境搭建

### 3.1 后端开发环境

#### 3.1.1 安装依赖
```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装解析器依赖
pip install pix2text paddleocr pymupdf pillow pytesseract tika camelot-py
```

#### 3.1.2 数据库配置
- 默认使用 SQLite 数据库
- 如需使用 MySQL，修改 `backend/app/config.py` 中的数据库连接字符串

#### 3.1.3 启动开发服务器
```bash
# 进入后端目录
cd backend

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 启动开发服务器
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 3.1.4 访问API文档
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### 3.2 前端开发环境

#### 3.2.1 安装依赖
```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install
```

#### 3.2.2 启动开发服务器
```bash
# 进入前端目录
cd frontend

# 启动开发服务器
npm run dev
```

#### 3.2.3 访问前端应用
- 应用地址: http://localhost:5173

## 4. 解析器开发

### 4.1 解析器架构

#### 4.1.1 BaseDocumentParser
所有解析器都继承自 `BaseDocumentParser` 抽象类，该类定义了统一的解析器接口：

```python
class BaseDocumentParser:
    def __init__(self):
        self.parser_name = self.__class__.__name__
        self.resource_level = "low"  # 资源级别: low, medium, high
    
    def can_parse(self, file_path: str) -> bool:
        """检查是否可以解析该文件"""
        raise NotImplementedError
    
    def parse(self, file_path: str, **kwargs) -> dict:
        """解析文件并返回结果"""
        raise NotImplementedError
```

#### 4.1.2 资源级别
- `low`: 基础资源，所有版本用户可用
- `medium`: 中级资源，专业版/企业版用户可用
- `high`: 高级资源，仅企业版用户可用

### 4.2 开发新解析器

#### 4.2.1 创建解析器类
```python
from app.services.document_parsers import BaseDocumentParser

class NewParser(BaseDocumentParser):
    def __init__(self):
        super().__init__()
        self.resource_level = "medium"  # 设置资源级别
    
    def can_parse(self, file_path: str) -> bool:
        # 检查文件类型是否支持
        return file_path.endswith('.ext')
    
    def parse(self, file_path: str, **kwargs) -> dict:
        # 实现解析逻辑
        result = {
            "content": "解析内容",
            "parameters": [],
            "tables": []
        }
        return result
```

#### 4.2.2 注册解析器
在 `backend/app/services/document_parsers/parser_manager.py` 中注册新解析器：

```python
from .new_parser import NewParser

class DocumentParserManager:
    def _load_parsers(self):
        # 加载现有解析器
        # ...
        
        # 添加新解析器
        try:
            self.parsers["new_parser"] = NewParser()
            logger.info(f"已加载解析器: NewParser")
        except Exception as e:
            logger.warning(f"加载解析器失败: NewParser - {e}")
```

### 4.3 解析器调用流程

1. **客户端请求**: 客户端上传文档并请求解析
2. **API路由**: `backend/app/routes/documents.py` 处理请求
3. **解析器服务**: `backend/app/services/document_parser.py` 调用解析器管理器
4. **解析器选择**: `ParserManager` 根据用户版本和文件类型选择合适的解析器
5. **执行解析**: 调用选定解析器的 `parse` 方法
6. **结果返回**: 将解析结果返回给客户端

## 5. 自动化功能开发

### 5.1 自动化架构

#### 5.1.1 核心组件
- **AutomationEngine**: 自动化引擎，负责任务调度和执行
- **TaskScheduler**: 任务调度器，管理任务的执行顺序和时间
- **ErrorHandler**: 错误处理器，处理自动化过程中的异常
- **Adapters**: 软件适配器，负责与不同软件交互
- **ParameterMappers**: 参数映射器，将通用参数映射到特定软件格式

#### 5.1.2 任务执行流程
1. 客户端提交自动化任务
2. AutomationEngine接收任务，创建任务对象
3. TaskScheduler将任务加入队列
4. 执行器从队列中取出任务，更新状态为RUNNING
5. 获取对应的软件适配器和参数映射器
6. 映射参数到目标软件格式
7. 执行自动化操作
8. 更新任务状态和结果
9. 返回执行结果

### 5.2 自动化服务开发

#### 5.2.1 核心类

```python
class AutomationEngine:
    """自动化引擎"""
    
    def submit_task(self, name: str, parameters: Dict[str, Any], 
                   target_software: str, adapter_type: str,
                   priority: int = 1, scheduled_time: datetime = None) -> str:
        """提交自动化任务"""
        # 实现任务提交逻辑
        pass
    
    def get_task_status(self, task_id: str) -> AutomationTask:
        """获取任务状态"""
        # 实现任务状态查询逻辑
        pass
    
    def get_task_result(self, task_id: str) -> AutomationResult:
        """获取任务结果"""
        # 实现任务结果查询逻辑
        pass
```

#### 5.2.2 任务模型

```python
class AutomationTask:
    """自动化任务"""
    
    def __init__(self, task_id: str, name: str, parameters: Dict[str, Any],
                 target_software: str, adapter_type: str, priority: int = 1,
                 scheduled_time: datetime = None):
        self.task_id = task_id
        self.name = name
        self.parameters = parameters
        self.target_software = target_software
        self.adapter_type = adapter_type
        self.priority = priority
        self.scheduled_time = scheduled_time
        self.status = TaskStatus.PENDING
        self.created_time = datetime.now()
        self.started_time = None
        self.completed_time = None
        self.result = None
        self.retry_count = 0
        self.max_retries = 3
        self.progress = 0
```

#### 5.2.3 结果模型

```python
class AutomationResult:
    """自动化执行结果"""
    
    def __init__(self, success: bool, status: AutomationStatus, message: str,
                 parameters_set: Dict[str, Any], execution_time: float,
                 error_details: str = None):
        self.success = success
        self.status = status
        self.message = message
        self.parameters_set = parameters_set
        self.execution_time = execution_time
        self.error_details = error_details
        self.output_files = []
        self.screenshots = []
```

### 5.3 添加新的软件适配器

#### 5.3.1 适配器接口

```python
class SoftwareAdapter:
    """软件适配器接口"""
    
    def execute_automation(self, parameters: Dict[str, Any]) -> AutomationResult:
        """执行自动化操作"""
        raise NotImplementedError
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证参数有效性"""
        raise NotImplementedError
    
    def get_supported_parameters(self) -> List[str]:
        """获取支持的参数列表"""
        raise NotImplementedError
```

#### 5.3.2 适配器实现示例

```python
class AspenPlusAdapter(SoftwareAdapter):
    """Aspen Plus适配器"""
    
    def execute_automation(self, parameters: Dict[str, Any]) -> AutomationResult:
        """执行Aspen Plus自动化"""
        try:
            # 实现Aspen Plus自动化逻辑
            # 1. 启动Aspen Plus
            # 2. 加载模拟文件
            # 3. 设置参数
            # 4. 运行模拟
            # 5. 获取结果
            
            return AutomationResult(
                success=True,
                status=AutomationStatus.COMPLETED,
                message="Aspen Plus模拟成功",
                parameters_set=parameters,
                execution_time=10.5
            )
        except Exception as e:
            return AutomationResult(
                success=False,
                status=AutomationStatus.FAILED,
                message=f"Aspen Plus模拟失败: {str(e)}",
                parameters_set={},
                execution_time=0.0,
                error_details=str(e)
            )
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证Aspen Plus参数"""
        required_params = ["simulation_file", "temperature", "pressure"]
        return all(param in parameters for param in required_params)
    
    def get_supported_parameters(self) -> List[str]:
        """获取支持的Aspen Plus参数"""
        return ["simulation_file", "temperature", "pressure", "flow_rate", "composition"]
```

#### 5.3.3 注册适配器

在自动化引擎初始化时注册适配器：

```python
class AutomationEngine:
    """自动化引擎"""
    
    def __init__(self):
        # 初始化适配器
        self.adapters = {
            "aspen_plus": AspenPlusAdapter(),
            "pro_ii": ProIIAdapter(),
            # 添加更多适配器
        }
        
        # 初始化参数映射器
        self.parameter_mappers = {
            "aspen_plus": AspenPlusParameterMapper(),
            "pro_ii": ProIIParameterMapper(),
            # 添加更多参数映射器
        }
```

## 6. API开发

### 6.1 API路由结构

#### 6.1.1 认证相关
- `POST /api/auth/login`: 用户登录
- `POST /api/auth/register`: 用户注册
- `GET /api/auth/me`: 获取当前用户信息

#### 6.1.2 文档相关
- `POST /api/documents/upload`: 上传文档
- `GET /api/documents`: 获取文档列表
- `GET /api/documents/{id}`: 获取文档详情
- `POST /api/documents/{id}/parse`: 解析文档
- `GET /api/documents/{id}/result`: 获取解析结果

#### 6.1.3 自动化相关
- `POST /api/automation/submit-task`: 提交自动化任务
- `POST /api/automation/batch-submit`: 批量提交任务
- `GET /api/automation/task-status/{task_id}`: 获取任务状态
- `GET /api/automation/task-result/{task_id}`: 获取任务结果
- `GET /api/automation/all-tasks`: 获取所有任务
- `POST /api/automation/cancel-task/{task_id}`: 取消任务
- `GET /api/automation/statistics`: 获取统计信息
- `POST /api/automation/start-engine`: 启动自动化引擎

#### 6.1.4 管理员相关
- `GET /api/admin/users`: 获取用户列表
- `PUT /api/admin/users/{id}`: 更新用户信息
- `DELETE /api/admin/users/{id}`: 删除用户

### 6.2 API开发规范

#### 6.2.1 路由设计
- 使用 RESTful API 设计风格
- 路由路径使用小写字母和连字符
- 资源命名使用复数形式

#### 6.2.2 响应格式
```json
{
  "code": 200,
  "message": "成功",
  "data": {}
}
```

#### 6.2.3 错误处理
- 使用 FastAPI 的 HTTPException 抛出异常
- 统一错误码和错误信息
- 提供详细的错误描述

## 7. 数据库开发

### 7.1 模型设计

所有数据库模型都继承自 `Base` 类，位于 `backend/app/models/` 目录下：

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(255))
    full_name = Column(String(100))
    role = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 版本和配额字段
    version = Column(String(20), default="basic")
    monthly_quota = Column(Integer, default=100)
    used_quota = Column(Integer, default=0)
    last_reset = Column(DateTime, default=datetime.utcnow)
```

### 7.2 数据库迁移

当前项目使用 SQLAlchemy 的 `Base.metadata.create_all(bind=engine)` 自动创建表，生产环境建议使用 Alembic 进行数据库迁移。

## 8. 代码规范

### 8.1 Python代码规范
- 遵循 PEP 8 规范
- 使用类型注解
- 函数和方法使用文档字符串
- 变量命名使用 snake_case
- 类命名使用 PascalCase

### 8.2 JavaScript/TypeScript代码规范
- 遵循 ESLint 规范
- 使用 TypeScript 类型注解
- 组件命名使用 PascalCase
- 变量和函数命名使用 camelCase
- 使用函数式组件和 Hooks

### 8.3 Git规范
- 提交信息使用中文
- 提交信息格式：`类型: 描述`
  - `feat`: 新功能
  - `fix`: 修复bug
  - `docs`: 文档更新
  - `style`: 代码格式调整
  - `refactor`: 代码重构
  - `test`: 测试代码
  - `chore`: 构建过程或辅助工具的变动

## 9. 测试

### 9.1 后端测试

#### 9.1.1 单元测试
使用 pytest 进行单元测试，测试文件位于 `backend/tests/` 目录下：

```bash
# 运行单元测试
cd backend
pytest
```

#### 9.1.2 API测试
可以使用 Swagger UI 或 Postman 进行 API 测试。

### 9.2 前端测试

#### 9.2.1 组件测试
使用 React Testing Library 进行组件测试：

```bash
# 运行组件测试
cd frontend
npm test
```

#### 9.2.2 E2E测试
使用 Cypress 进行端到端测试：

```bash
# 运行E2E测试
cd frontend
npx cypress open
```

## 10. 部署

### 10.1 后端部署

#### 10.1.1 生产环境依赖
```bash
# 安装生产依赖
cd backend
pip install -r requirements.txt
```

#### 10.1.2 使用 Gunicorn 运行
```bash
# 使用Gunicorn运行后端服务
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

### 10.2 前端部署

#### 10.2.1 构建生产版本
```bash
# 构建生产版本
cd frontend
npm run build
```

#### 10.2.2 使用 Nginx 部署
```nginx
server {
    listen 80;
    server_name example.com;
    
    location / {
        root /path/to/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 11. 开发流程

### 11.1 分支管理
- `main`: 主分支，用于发布生产版本
- `develop`: 开发分支，用于集成新功能
- `feature/*`: 功能分支，用于开发新功能
- `bugfix/*`: 修复分支，用于修复bug

### 11.2 开发步骤
1. 从 `develop` 分支创建功能分支
2. 开发新功能或修复bug
3. 编写测试用例
4. 提交代码并创建 Pull Request
5. 代码审查通过后合并到 `develop` 分支
6. 定期从 `develop` 分支合并到 `main` 分支进行发布

## 12. 常见问题

### 12.1 解析器依赖问题
- **问题**: 解析器依赖安装失败
- **解决方法**: 确保已安装所有必要的系统依赖，如 Tesseract、Ghostscript 等

### 12.2 数据库连接问题
- **问题**: 无法连接到数据库
- **解决方法**: 检查数据库配置是否正确，确保数据库服务正在运行

### 12.3 CORS问题
- **问题**: 前端无法访问后端API
- **解决方法**: 检查后端 CORS 配置，确保允许前端域名访问

## 13. 最佳实践

### 13.1 代码复用
- 提取通用功能为工具函数
- 使用抽象类和接口定义统一的API
- 避免重复代码

### 13.2 性能优化
- 使用异步编程提高并发处理能力
- 优化数据库查询，添加适当的索引
- 缓存频繁访问的数据
- 优化解析器性能，减少资源消耗

### 13.3 安全性
- 使用 HTTPS 协议
- 实现适当的认证和授权机制
- 对用户输入进行验证和清洗
- 保护敏感数据，如密码哈希存储
- 定期更新依赖，修复安全漏洞

## 14. 联系方式

- **项目地址**: https://github.com/UnveilChem/Aifiller
- **开发团队**: UnveilChem开发团队
- **技术支持**: dev@unveilchem.com

---

**文档版本**：1.0
**编制日期**：2025-11-28
**编制人**：Aifiller 开发团队