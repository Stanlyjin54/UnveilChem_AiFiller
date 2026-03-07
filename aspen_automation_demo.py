#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aspen Plus 自动化集成演示脚本
展示如何将文档处理与Aspen Plus自动化工作流程相结合
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AspenAutomationDemo:
    """Aspen Plus自动化演示类"""
    
    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.demo_aspen_params = {
            "temperature": 85.0,
            "pressure": 1.0,
            "reflux_ratio": 2.5,
            "number_stages": 20,
            "reboiler_duty": 1e6,
            "condenser_duty": 8e5,
            "feed_flow_rate": 100.0,
            "feed_composition": {
                "benzene": 0.4,
                "toluene": 0.6
            }
        }
    
    def demo_single_task_submission(self):
        """演示单任务提交"""
        print("\n" + "="*50)
        print("演示1: 单个Aspen Plus自动化任务")
        print("="*50)
        
        task_data = {
            "name": "精馏塔参数优化",
            "target_software": "Aspen Plus",
            "adapter_type": "aspen_plus",
            "parameters": {
                "temperature": 85.0,
                "pressure": 1.0,
                "reflux_ratio": 2.5,
                "number_stages": 20
            },
            "priority": 5
        }
        
        print(f"任务名称: {task_data['name']}")
        print(f"目标软件: {task_data['target_software']}")
        print(f"参数数量: {len(task_data['parameters'])}")
        print(f"参数详情: {json.dumps(task_data['parameters'], indent=2, ensure_ascii=False)}")
        
        # 模拟API调用
        print("\n模拟API调用:")
        print(f"POST {self.api_base}/api/automation/submit-task")
        print(f"Request Body: {json.dumps(task_data, indent=2, ensure_ascii=False)}")
        print("Response: {'task_id': 'task_12345', 'status': 'submitted'}")
        
        return "task_12345"
    
    def demo_batch_processing(self):
        """演示批量处理工作流程"""
        print("\n" + "="*50)
        print("演示2: 批量文档处理到Aspen Plus参数设置")
        print("="*50)
        
        # 模拟多个工艺参数文档
        documents = [
            {"name": "实验报告_20240115.pdf", "temperature": 80.0, "pressure": 1.2},
            {"name": "设计文档_v2.pdf", "temperature": 85.0, "pressure": 1.0},
            {"name": "优化方案.pdf", "temperature": 82.0, "pressure": 1.1}
        ]
        
        batch_tasks = []
        for i, doc in enumerate(documents, 1):
            task = {
                "name": f"文档处理_{i}_{doc['name']}",
                "target_software": "Aspen Plus",
                "adapter_type": "aspen_plus",
                "parameters": {
                    "extracted_from_document": doc['name'],
                    "temperature": doc['temperature'],
                    "pressure": doc['pressure'],
                    "reflux_ratio": 2.0 + i * 0.2,
                    "number_stages": 15 + i
                }
            }
            batch_tasks.append(task)
        
        print(f"批量任务数量: {len(batch_tasks)}")
        print("\n任务详情:")
        for i, task in enumerate(batch_tasks, 1):
            print(f"\n任务 {i}:")
            print(f"  名称: {task['name']}")
            print(f"  来源文档: {task['parameters']['extracted_from_document']}")
            print(f"  温度: {task['parameters']['temperature']}°C")
            print(f"  压力: {task['parameters']['pressure']} bar")
        
        print(f"\n模拟API调用:")
        print(f"POST {self.api_base}/api/automation/batch-submit")
        print("Request Body:")
        print(json.dumps({
            "tasks": batch_tasks,
            "wait_for_completion": True
        }, indent=2, ensure_ascii=False))
        
        return ["task_batch_1", "task_batch_2", "task_batch_3"]
    
    def demo_document_to_aspen_workflow(self):
        """演示完整的文档到Aspen Plus工作流程"""
        print("\n" + "="*50)
        print("演示3: 文档解析到Aspen Plus自动设置完整流程")
        print("="*50)
        
        workflow_steps = [
            {
                "step": 1,
                "name": "文档输入",
                "description": "用户上传包含工艺参数的PDF文档",
                "input": "工艺参数设计文档.pdf",
                "output": "文档文件对象"
            },
            {
                "step": 2,
                "name": "文档解析",
                "description": "parsers模块自动解析PDF文档",
                "input": "PDF文档",
                "output": {
                    "extracted_parameters": {
                        "操作温度": "85°C",
                        "操作压力": "1.0 bar",
                        "回流比": "2.5",
                        "理论板数": "20块",
                        "进料流量": "100 kmol/h"
                    },
                    "confidence_scores": {
                        "温度": 0.95,
                        "压力": 0.98,
                        "回流比": 0.92
                    }
                }
            },
            {
                "step": 3,
                "name": "参数验证",
                "description": "验证提取参数的有效性和完整性",
                "input": "提取的参数",
                "output": {
                    "validated_parameters": {
                        "temperature": 85.0,
                        "pressure": 1.0,
                        "reflux_ratio": 2.5,
                        "number_stages": 20,
                        "feed_flow_rate": 100.0
                    },
                    "validation_report": "所有参数验证通过"
                }
            },
            {
                "step": 4,
                "name": "Aspen任务创建",
                "description": "创建Aspen Plus自动化任务",
                "input": "验证后的参数",
                "output": {
                    "task_id": "aspen_task_001",
                    "target_software": "Aspen Plus",
                    "status": "pending"
                }
            },
            {
                "step": 5,
                "name": "自动化执行",
                "description": "系统自动连接到Aspen Plus并设置参数",
                "input": "Aspen任务",
                "output": {
                    "aspen_connection": "success",
                    "parameters_set": 5,
                    "simulation_run": "completed",
                    "results_extracted": True
                }
            }
        ]
        
        for step_info in workflow_steps:
            print(f"\n步骤 {step_info['step']}: {step_info['name']}")
            print(f"  描述: {step_info['description']}")
            print(f"  输入: {step_info['input']}")
            print(f"  输出: {json.dumps(step_info['output'], indent=6, ensure_ascii=False)}")
            time.sleep(0.5)  # 模拟处理时间
        
        return "workflow_completed"
    
    def demo_integration_scenarios(self):
        """演示具体集成场景"""
        print("\n" + "="*50)
        print("演示4: 实际应用场景")
        print("="*50)
        
        scenarios = [
            {
                "name": "实验室数据快速验证",
                "description": "将实验报告中的数据直接应用到Aspen模型",
                "input": "实验数据报告.pdf",
                "process": [
                    "解析实验报告",
                    "提取操作条件",
                    "更新Aspen模型参数",
                    "运行模拟并对比实验数据"
                ],
                "benefit": "减少90%的手动输入时间"
            },
            {
                "name": "设计文档批量更新",
                "description": "批量处理多个设计方案的参数更新",
                "input": "多个Aspen案例文件",
                "process": [
                    "扫描设计方案文档",
                    "提取改进参数",
                    "批量更新Aspen案例",
                    "生成对比分析报告"
                ],
                "benefit": "支持快速方案迭代"
            },
            {
                "name": "工艺优化自动化",
                "description": "基于文献数据自动优化工艺参数",
                "input": "最新工艺优化文献",
                "process": [
                    "解析优化算法参数",
                    "应用新参数到现有模型",
                    "运行优化模拟",
                    "生成优化建议报告"
                ],
                "benefit": "持续工艺改进"
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n场景 {i}: {scenario['name']}")
            print(f"  描述: {scenario['description']}")
            print(f"  输入: {scenario['input']}")
            print(f"  处理流程:")
            for j, process_step in enumerate(scenario['process'], 1):
                print(f"    {j}. {process_step}")
            print(f"  效益: {scenario['benefit']}")
    
    def demo_api_integration_example(self):
        """演示API集成示例代码"""
        print("\n" + "="*50)
        print("演示5: Python API集成代码示例")
        print("="*50)
        
        integration_code = '''
# aspen_integration.py - Python集成示例
import requests
import asyncio
from typing import Dict, Any

class UnveilChemAspenClient:
    """UnveilChem-Aspen Plus客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    async def process_document_to_aspen(self, document_path: str) -> Dict[str, Any]:
        """处理文档到Aspen Plus的工作流程"""
        
        # 1. 提交文档处理任务
        task_data = {
            "name": f"文档处理 - {Path(document_path).name}",
            "target_software": "Aspen Plus",
            "adapter_type": "aspen_plus",
            "parameters": {
                "document_path": document_path,
                "auto_extract": True,
                "validation_required": True
            },
            "priority": 8
        }
        
        # 2. 提交到API
        response = await self._async_post(
            f"{self.base_url}/api/automation/submit-task", 
            json=task_data
        )
        
        task_id = response.json()["task_id"]
        
        # 3. 监控任务状态
        result = await self._monitor_task(task_id)
        
        return {
            "task_id": task_id,
            "status": result["status"],
            "extracted_parameters": result.get("result", {}),
            "execution_time": result.get("execution_time", 0)
        }
    
    async def batch_update_aspen_cases(self, case_updates: List[Dict]) -> Dict[str, Any]:
        """批量更新Aspen案例参数"""
        
        batch_data = {
            "batch_id": f"batch_{int(time.time())}",
            "name": "批量Aspen案例更新",
            "software_type": "aspen_plus",
            "parameter_sets": case_updates
        }
        
        response = await self._async_post(
            f"{self.base_url}/api/automation/batch-submit",
            json=batch_data
        )
        
        return response.json()
    
    async def _async_post(self, url: str, **kwargs):
        """异步POST请求"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self.session.post(url, **kwargs)
        )
    
    async def _monitor_task(self, task_id: str, timeout: int = 300) -> Dict:
        """监控任务状态"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = await self._async_get(
                f"{self.base_url}/api/automation/task-status/{task_id}"
            )
            
            task_status = response.json()
            if task_status["status"] in ["completed", "failed"]:
                return task_status
            
            await asyncio.sleep(5)  # 每5秒检查一次
        
        return {"status": "timeout"}

# 使用示例
async def main():
    client = UnveilChemAspenClient()
    
    # 示例1: 处理单个文档
    result = await client.process_document_to_aspen("实验报告.pdf")
    print(f"处理结果: {result}")
    
    # 示例2: 批量更新
    updates = [
        {
            "name": "更新案例1",
            "case_path": "distillation_1.bkp",
            "new_temperature": 85.0
        },
        {
            "name": "更新案例2", 
            "case_path": "distillation_2.bkp",
            "new_temperature": 82.0
        }
    ]
    
    batch_result = await client.batch_update_aspen_cases(updates)
    print(f"批量更新结果: {batch_result}")

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        print(integration_code)
        
        return integration_code
    
    def run_all_demos(self):
        """运行所有演示"""
        print("=" * 70)
        print("UnveilChem_AI_DocAnalyzer + Aspen Plus 自动化集成演示")
        print("=" * 70)
        print(f"演示开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 演示1: 单任务
        task_id = self.demo_single_task_submission()
        
        # 演示2: 批量处理
        batch_tasks = self.demo_batch_processing()
        
        # 演示3: 完整工作流程
        workflow_result = self.demo_document_to_aspen_workflow()
        
        # 演示4: 应用场景
        self.demo_integration_scenarios()
        
        # 演示5: 代码示例
        self.demo_api_integration_example()
        
        # 总结
        print("\n" + "="*50)
        print("演示总结")
        print("="*50)
        print("✅ 单任务自动化: 成功")
        print("✅ 批量文档处理: 成功") 
        print("✅ 完整工作流程: 成功")
        print("✅ 应用场景展示: 完成")
        print("✅ API集成代码: 提供")
        print(f"\n演示结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n下一步操作建议:")
        print("1. 启动系统服务: python run_backend.py")
        print("2. 访问API文档: http://localhost:8000/docs")
        print("3. 上传工艺文档测试自动化流程")
        print("4. 集成到现有的Aspen Plus工作流程中")

if __name__ == "__main__":
    demo = AspenAutomationDemo()
    demo.run_all_demos()