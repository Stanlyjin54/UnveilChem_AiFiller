# Aspen Plus 自动化集成指南

## 系统概述

您的UnveilChem_AI_DocAnalyzer系统包含完整的Aspen Plus集成能力，可以通过以下方式实现自动化工作流程：

### 1. 核心组件
- **Aspen Plus适配器** (`backend/app/services/automation/aspen_plus.py`)
- **自动化API接口** (`backend/app/routes/automation.py`) 
- **文档解析器模块** (`parsers/`)
- **任务调度系统** (`backend/app/services/automation/scheduler.py`)

## 集成方案

### 方案一：直接API调用模式

#### 1.1 启动系统服务
```bash
# 启动后端服务
cd d:\UnveilChem_AI_DocAnalyzer
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 或者使用开发服务器
python run_backend.py
```

#### 1.2 提交Aspen Plus自动化任务
```python
import requests
import json

# API基础地址
BASE_URL = "http://localhost:8000"

# 1. 提交参数设置任务
task_data = {
    "name": "设置精馏塔参数",
    "parameters": {
        "temperature": 85.0,  # °C
        "pressure": 1.0,      # bar  
        "reflux_ratio": 2.5,
        "number_stages": 20,
        "reboiler_duty": 1e6  # W
    },
    "target_software": "Aspen Plus",
    "adapter_type": "aspen_plus",
    "priority": 5
}

response = requests.post(f"{BASE_URL}/api/automation/submit-task", json=task_data)
task_id = response.json()["task_id"]

# 2. 检查任务状态
status_response = requests.get(f"{BASE_URL}/api/automation/task-status/{task_id}")
print(f"任务状态: {status_response.json()}")
```

### 方案二：文档驱动的自动化模式

#### 2.1 文档解析到参数自动转换
```python
# 完整工作流程：文档 -> 参数提取 -> Aspen Plus设置
import asyncio
from backend.services.parsers import UnifiedDocumentParser
from backend.services.automation import AutomationService

async def document_to_aspen_workflow(document_path):
    """文档到Aspen Plus的完整工作流程"""
    
    # 1. 解析文档提取参数
    parser = UnifiedDocumentParser()
    parsed_data = await parser.parse_document(document_path)
    
    # 2. 提取Aspen相关参数
    aspen_params = {
        "temperature": parsed_data.get("操作温度", 85.0),
        "pressure": parsed_data.get("操作压力", 1.0), 
        "flow_rate": parsed_data.get("进料流量", 100.0),
        "composition": parsed_data.get("组分", {"benzene": 0.5, "toluene": 0.5}),
        "reboiler_duty": parsed_data.get("再沸器热负荷", 1e6),
        "reflux_ratio": parsed_data.get("回流比", 2.5)
    }
    
    # 3. 创建自动化任务
    automation_service = AutomationService()
    task_data = {
        "name": f"文档参数导入 - {document_path}",
        "software_type": "aspen_plus",
        "parameters": aspen_params,
        "priority": "high"
    }
    
    # 4. 提交执行
    result = await automation_service.create_task(task_data, "user_id")
    return result

# 使用示例
# result = await document_to_aspen_workflow("工艺参数文档.pdf")
```

#### 2.2 批量处理工作流程
```python
async def batch_document_processing(document_folder, aspen_case_path):
    """批量处理文档并应用到Aspen Plus"""
    
    import os
    from pathlib import Path
    
    # 获取所有PDF文档
    pdf_files = list(Path(document_folder).glob("*.pdf"))
    
    # 创建批量任务
    batch_tasks = []
    for pdf_file in pdf_files:
        task = {
            "name": f"批量处理 - {pdf_file.name}",
            "parameters": {"document_path": str(pdf_file)},
            "target_software": "Aspen Plus",
            "adapter_type": "aspen_plus"
        }
        batch_tasks.append(task)
    
    # 提交批量任务
    automation_service = AutomationService()
    batch_data = {
        "batch_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "name": "批量文档处理",
        "software_type": "aspen_plus", 
        "parameter_sets": batch_tasks
    }
    
    result = await automation_service.create_batch_tasks(batch_data, "user_id")
    return result
```

### 方案三：集成的Aspen Plus宏命令模式

#### 3.1 创建Aspen Plus自动化宏
在Aspen Plus中创建自动化宏文件：

```vba
' AspenPlus_Automation.bas
Sub AutoParameterSetup()
    ' 连接到UnveilChem系统
    Dim http As Object
    Set http = CreateObject("WinHttp.WinHttpRequest.5.1")
    
    ' 设置API地址
    apiUrl = "http://localhost:8000/api/automation/submit-task"
    
    ' 构建任务数据
    Dim taskData As String
    taskData = "{"
    taskData = taskData & """name"":""Aspen自动参数设置"","
    taskData = taskData & """target_software"":""Aspen Plus"","
    taskData = taskData & """adapter_type"":""aspen_plus"","
    taskData = taskData & """parameters"":{"
    taskData = taskData & """temperature"":""& GetParam("TEMP") &"","
    taskData = taskData & """pressure"":""& GetParam("PRES") &"""
    taskData = taskData & "}}"
    
    ' 发送请求
    http.Open "POST", apiUrl, False
    http.setRequestHeader "Content-Type", "application/json"
    http.Send taskData
    
    MsgBox "参数已发送到自动化系统", vbInformation
End Sub

Function GetParam(paramName As String) As String
    ' 从当前Aspen案例获取参数
    GetParam = Application.ActiveDocument.Data.Tables("STREAMS").Item(paramName).Value
End Function
```

#### 3.2 Python集成脚本
```python
# aspen_bridge.py - 作为Aspen Plus和系统的桥梁
import win32com.client
import requests
import json
import time

class AspenSystemBridge:
    """Aspen Plus与UnveilChem系统的桥接器"""
    
    def __init__(self):
        self.aspen_app = None
        self.api_base = "http://localhost:8000"
    
    def connect_aspen(self):
        """连接到Aspen Plus"""
        try:
            self.aspen_app = win32com.client.Dispatch("Apwn.Document")
            return True
        except:
            return False
    
    def sync_case_to_system(self, case_path):
        """将当前Aspen案例数据同步到系统"""
        
        # 1. 提取案例关键参数
        case_data = self.extract_case_parameters(case_path)
        
        # 2. 提交到系统进行文档分析
        task_data = {
            "name": f"Aspen案例分析 - {case_path}",
            "parameters": case_data,
            "target_software": "Aspen Plus",
            "adapter_type": "aspen_plus"
        }
        
        # 3. 发送API请求
        response = requests.post(
            f"{self.api_base}/api/automation/submit-task",
            json=task_data
        )
        
        return response.json()
    
    def extract_case_parameters(self, case_path):
        """从Aspen案例提取参数"""
        # 这里可以根据需要提取具体的工艺参数
        parameters = {
            "case_path": case_path,
            "streams": self.get_streams_data(),
            "blocks": self.get_blocks_data(),
            "components": self.get_components_data()
        }
        return parameters
    
    def get_streams_data(self):
        """获取物流数据"""
        try:
            streams_table = self.aspen_app.Data.Tables("STREAMS")
            # 提取物流数据
            return {"sample": "data"}  # 实际实现需要根据Aspen对象模型
        except:
            return {}
```

## 实际使用场景

### 场景1：工艺参数文档自动导入
1. **输入**：包含工艺参数的PDF文档（实验报告、设计文档等）
2. **处理**：parsers模块自动解析文档，提取温度、压力、流量等参数
3. **输出**：自动设置到Aspen Plus相应单元操作中
4. **优势**：消除手动输入错误，提高设计效率

### 场景2：批量案例参数更新
1. **输入**：多个Aspen案例文件
2. **处理**：系统批量读取案例，识别需要更新的参数
3. **输出**：批量更新参数并重新运行模拟
4. **优势**：大幅减少重复性工作

### 场景3：文档与仿真联动
1. **输入**：新文献或实验数据文档
2. **处理**：解析文档，更新现有Aspen案例参数
3. **输出**：生成新的仿真结果
4. **优势**：快速验证新数据对工艺的影响

## API接口详解

### 主要端点
- `POST /api/automation/submit-task` - 提交单个任务
- `POST /api/automation/batch-submit` - 批量提交任务  
- `GET /api/automation/task-status/{task_id}` - 获取任务状态
- `GET /api/automation/tasks` - 获取用户任务列表
- `GET /api/automation/statistics` - 获取系统统计

### 请求示例
```json
{
    "name": "精馏塔参数设置",
    "target_software": "Aspen Plus",
    "adapter_type": "aspen_plus",
    "parameters": {
        "temperature": 85.0,
        "pressure": 1.0,
        "reflux_ratio": 2.5,
        "number_stages": 20
    },
    "priority": 5,
    "scheduled_time": "2024-01-15T10:00:00"
}
```

## 性能优化建议

1. **并发控制**：合理设置最大并发任务数（建议3-5个）
2. **批量处理**：使用批量API减少网络开销
3. **错误重试**：启用自动重试机制，提高任务成功率
4. **监控告警**：配置错误通知，及时处理异常

## 部署配置

### 环境要求
- Python 3.8+
- Windows系统（用于COM接口）
- Aspen Plus 12.0+ 已安装
- 依赖包：win32com, fastapi, uvicorn等

### 配置文件
```yaml
# config/automation.yaml
automation:
  max_concurrent_tasks: 5
  default_timeout: 300
  enable_notifications: true
  aspen:
    connection_timeout: 60
    simulation_timeout: 300
```

通过以上方案，您可以实现从文档到Aspen Plus的完全自动化工作流程，显著提高化工设计效率。