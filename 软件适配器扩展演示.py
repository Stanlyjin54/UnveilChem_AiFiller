#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UnveilChem智能参数录入助手 - 软件适配器扩展演示
展示如何启用和管理各种软件适配器
"""

import sys
import os
import logging
from typing import Dict, List, Optional
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SoftwareAdapterManager:
    """软件适配器管理器"""
    
    def __init__(self):
        self.adapters = {}
        self.parameter_mappers = {}
        self.software_info = {
            "aspen_plus": {
                "name": "Aspen Plus",
                "version_support": "2019+",
                "category": "化工流程模拟",
                "primary_functions": ["案例管理", "参数设置", "流程运行", "结果分析"]
            },
            "dwsim": {
                "name": "DWSIM",
                "version_support": "6.0+",
                "category": "化工流程模拟",
                "primary_functions": ["仿真加载", "单元操作", "数据交换", "成本分析"]
            },
            "pro_ii": {
                "name": "PRO/II", 
                "version_support": "10.0+",
                "category": "化工流程模拟",
                "primary_functions": ["案例操作", "设备参数", "结果导出", "优化分析"]
            },
            "chemcad": {
                "name": "ChemCAD",
                "version_support": "7.0+",
                "category": "化工流程模拟", 
                "primary_functions": ["工艺参数", "设备规格", "物性数据", "能效分析"]
            },
            "autocad": {
                "name": "AutoCAD",
                "version_support": "2018+",
                "category": "CAD设计",
                "primary_functions": ["图纸操作", "几何参数", "工程图生成", "尺寸标注"]
            },
            "solidworks": {
                "name": "SolidWorks",
                "version_support": "2018+",
                "category": "3D设计",
                "primary_functions": ["3D建模", "特征参数", "工程图导出", "仿真分析"]
            },
            "excel": {
                "name": "Excel",
                "version_support": "2016+",
                "category": "数据处理",
                "primary_functions": ["数据导入", "公式计算", "图表生成", "报告输出"]
            }
        }
    
    def list_available_software(self) -> List[str]:
        """列出所有可用的软件"""
        return list(self.software_info.keys())
    
    def get_software_info(self, software_type: str) -> Optional[Dict]:
        """获取软件信息"""
        return self.software_info.get(software_type)
    
    def enable_software_adapter(self, software_type: str, version: str = None) -> bool:
        """启用软件适配器"""
        try:
            if software_type not in self.software_info:
                logger.error(f"不支持的软件: {software_type}")
                return False
            
            logger.info(f"正在启用 {software_type} 适配器...")
            
            # 模拟适配器初始化（实际使用时会创建真实适配器实例）
            if software_type == "aspen_plus":
                # 实际实现会使用: from backend.app.services.automation import AspenPlusAdapter
                adapter = self._create_mock_adapter("aspen_plus", version)
                
            elif software_type == "autocad":
                adapter = self._create_mock_adapter("autocad", version or "2024")
                
            elif software_type == "solidworks":
                adapter = self._create_mock_adapter("solidworks", version or "2024")
                
            elif software_type == "excel":
                adapter = self._create_mock_adapter("excel", version or "2019")
                
            else:
                # 其他软件的模拟适配器
                adapter = self._create_mock_adapter(software_type, version)
            
            self.adapters[software_type] = adapter
            
            # 初始化参数映射器
            self._initialize_parameter_mapper(software_type)
            
            logger.info(f"{software_type} 适配器启用成功")
            return True
            
        except Exception as e:
            logger.error(f"启用 {software_type} 适配器失败: {e}")
            return False
    
    def _create_mock_adapter(self, software_type: str, version: str = None):
        """创建模拟适配器（演示用）"""
        return {
            "software_type": software_type,
            "version": version,
            "connected": False,
            "active": True,
            "last_used": None,
            "connection_count": 0
        }
    
    def _initialize_parameter_mapper(self, software_type: str):
        """初始化参数映射器"""
        # 模拟不同软件的参数映射配置
        if software_type == "aspen_plus":
            self.parameter_mappers[software_type] = {
                "temperature": {"software_field": "TEMP", "unit": "C", "validation": "range"},
                "pressure": {"software_field": "PRES", "unit": "bar", "validation": "range"},
                "flow_rate": {"software_field": "FLOW", "unit": "kmol/hr", "validation": "positive"}
            }
        elif software_type == "autocad":
            self.parameter_mappers[software_type] = {
                "diameter": {"software_field": "DIAMETER", "unit": "mm", "validation": "positive"},
                "length": {"software_field": "LENGTH", "unit": "mm", "validation": "positive"},
                "angle": {"software_field": "ANGLE", "unit": "degree", "validation": "range"}
            }
        elif software_type == "solidworks":
            self.parameter_mappers[software_type] = {
                "diameter": {"software_field": "D1@Sketch1", "unit": "m", "validation": "positive"},
                "length": {"software_field": "D2@Extrude1", "unit": "m", "validation": "positive"},
                "density": {"software_field": "Density", "unit": "kg/m3", "validation": "range"}
            }
        elif software_type == "excel":
            self.parameter_mappers[software_type] = {
                "cell_value": {"software_field": "CELL_VALUE", "unit": "any", "validation": "none"},
                "formula": {"software_field": "FORMULA", "unit": "text", "validation": "regex"}
            }
    
    def connect_software(self, software_type: str) -> bool:
        """连接到软件"""
        try:
            if software_type not in self.adapters:
                logger.error(f"适配器未启用: {software_type}")
                return False
            
            adapter = self.adapters[software_type]
            logger.info(f"正在连接 {software_type}...")
            
            # 模拟连接过程
            import time
            time.sleep(0.5)  # 模拟连接延迟
            
            adapter["connected"] = True
            adapter["connection_count"] += 1
            adapter["last_used"] = "2024-01-01 12:00:00"
            
            logger.info(f"成功连接到 {software_type}")
            return True
            
        except Exception as e:
            logger.error(f"连接 {software_type} 失败: {e}")
            return False
    
    def set_parameters(self, software_type: str, parameters: Dict) -> Dict:
        """设置参数"""
        try:
            if software_type not in self.adapters:
                raise ValueError(f"适配器未启用: {software_type}")
            
            if not self.adapters[software_type]["connected"]:
                raise ValueError(f"未连接到 {software_type}")
            
            param_mapper = self.parameter_mappers.get(software_type, {})
            results = {}
            
            logger.info(f"为 {software_type} 设置 {len(parameters)} 个参数")
            
            for param_name, param_value in parameters.items():
                try:
                    # 查找参数映射
                    mapping = param_mapper.get(param_name)
                    if mapping:
                        # 验证参数
                        if self._validate_parameter(param_value, mapping["validation"]):
                            # 模拟参数设置
                            results[param_name] = {
                                "value": param_value,
                                "software_field": mapping["software_field"],
                                "unit": mapping["unit"],
                                "status": "success"
                            }
                        else:
                            results[param_name] = {
                                "value": param_value,
                                "status": "validation_failed",
                                "error": f"参数验证失败: {param_name}"
                            }
                    else:
                        results[param_name] = {
                            "value": param_value,
                            "status": "no_mapping",
                            "error": f"未找到参数映射: {param_name}"
                        }
                        
                except Exception as e:
                    results[param_name] = {
                        "value": param_value,
                        "status": "error",
                        "error": str(e)
                    }
            
            return results
            
        except Exception as e:
            logger.error(f"设置参数失败: {e}")
            return {"error": str(e)}
    
    def _validate_parameter(self, value: any, validation_type: str) -> bool:
        """验证参数值"""
        try:
            if validation_type == "positive":
                return float(value) > 0
            elif validation_type == "range":
                return -273.15 <= float(value) <= 1000
            elif validation_type == "none":
                return True
            else:
                return True
        except:
            return False
    
    def get_adapter_status(self) -> Dict:
        """获取所有适配器状态"""
        status = {}
        for software_type, adapter in self.adapters.items():
            status[software_type] = {
                "connected": adapter["connected"],
                "active": adapter["active"],
                "version": adapter["version"],
                "connection_count": adapter["connection_count"],
                "last_used": adapter["last_used"]
            }
        return status
    
    def batch_enable_adapters(self, software_list: List[str]) -> Dict[str, bool]:
        """批量启用适配器"""
        results = {}
        for software in software_list:
            results[software] = self.enable_software_adapter(software)
        return results
    
    def get_automation_workflow(self, workflow_type: str) -> Dict:
        """获取自动化工作流程"""
        workflows = {
            "chemical_process": {
                "name": "化工流程自动化",
                "software_sequence": ["aspen_plus", "excel", "autocad"],
                "steps": [
                    {"step": 1, "action": "启动Aspen Plus流程模拟", "software": "aspen_plus"},
                    {"step": 2, "action": "提取工艺参数", "software": "aspen_plus"},
                    {"step": 3, "action": "生成Excel报告", "software": "excel"},
                    {"step": 4, "action": "创建AutoCAD工程图", "software": "autocad"}
                ]
            },
            "design_optimization": {
                "name": "设计优化自动化",
                "software_sequence": ["solidworks", "excel", "aspen_plus"],
                "steps": [
                    {"step": 1, "action": "启动SolidWorks设计", "software": "solidworks"},
                    {"step": 2, "action": "设置设计参数", "software": "solidworks"},
                    {"step": 3, "action": "导入Aspen Plus进行仿真", "software": "aspen_plus"},
                    {"step": 4, "action": "Excel数据分析", "software": "excel"}
                ]
            }
        }
        return workflows.get(workflow_type, {})


def demo_software_adapter_management():
    """演示软件适配器管理"""
    print("=" * 60)
    print("UnveilChem智能参数录入助手 - 软件适配器扩展演示")
    print("=" * 60)
    
    # 创建适配器管理器
    manager = SoftwareAdapterManager()
    
    # 1. 列出所有可用软件
    print("\n📋 1. 可用的软件适配器:")
    available_software = manager.list_available_software()
    for software in available_software:
        info = manager.get_software_info(software)
        print(f"  • {info['name']} ({software}) - {info['category']}")
        print(f"    支持版本: {info['version_support']}")
        print(f"    主要功能: {', '.join(info['primary_functions'])}")
        print()
    
    # 2. 批量启用化工软件适配器
    print("🚀 2. 启用化工软件适配器:")
    chemical_software = ["aspen_plus", "dwsim", "pro_ii", "chemcad"]
    enable_results = manager.batch_enable_adapters(chemical_software)
    for software, success in enable_results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  • {software}: {status}")
    
    # 3. 启用CAD软件适配器
    print("\n🎨 3. 启用CAD软件适配器:")
    cad_software = ["autocad", "solidworks"]
    for software in cad_software:
        success = manager.enable_software_adapter(software)
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  • {software}: {status}")
    
    # 4. 启用数据处理软件适配器
    print("\n📊 4. 启用数据处理软件适配器:")
    success = manager.enable_software_adapter("excel")
    print(f"  • excel: {'✅ 成功' if success else '❌ 失败'}")
    
    # 5. 连接软件
    print("\n🔗 5. 连接已启用的软件:")
    enabled_software = [s for s, success in enable_results.items() if success]
    enabled_software.extend(["autocad", "solidworks", "excel"])
    
    for software in enabled_software[:3]:  # 只连接前3个以节省时间
        success = manager.connect_software(software)
        status = "✅ 连接成功" if success else "❌ 连接失败"
        print(f"  • {software}: {status}")
    
    # 6. 设置参数示例
    print("\n⚙️  6. 设置软件参数示例:")
    
    # Aspen Plus参数设置
    aspen_params = {
        "temperature": 150.0,  # °C
        "pressure": 5.0,       # bar
        "flow_rate": 100.0     # kmol/hr
    }
    print("  • Aspen Plus参数:")
    aspen_results = manager.set_parameters("aspen_plus", aspen_params)
    for param, result in aspen_results.items():
        if result["status"] == "success":
            print(f"    - {param}: {result['value']} {result['unit']} ({result['software_field']})")
        else:
            print(f"    - {param}: {result['status']} - {result.get('error', '')}")
    
    # AutoCAD参数设置
    autocad_params = {
        "diameter": 500.0,     # mm
        "length": 2000.0,      # mm
        "angle": 90.0          # degree
    }
    print("  • AutoCAD参数:")
    autocad_results = manager.set_parameters("autocad", autocad_params)
    for param, result in autocad_results.items():
        if isinstance(result, dict) and "status" in result:
            if result["status"] == "success":
                print(f"    - {param}: {result['value']} {result['unit']} ({result['software_field']})")
            else:
                print(f"    - {param}: {result['status']} - {result.get('error', '')}")
        else:
            print(f"    - {param}: 错误 - {result}")
    
    # 7. 查看适配器状态
    print("\n📈 7. 适配器状态概览:")
    status = manager.get_adapter_status()
    for software, info in status.items():
        connection_status = "🔗 已连接" if info["connected"] else "⏸️  未连接"
        print(f"  • {software}: {connection_status}")
        print(f"    版本: {info['version']}, 连接次数: {info['connection_count']}")
    
    # 8. 自动化工作流程示例
    print("\n🔄 8. 自动化工作流程示例:")
    workflow = manager.get_automation_workflow("chemical_process")
    print(f"  工作流: {workflow['name']}")
    for step in workflow['steps']:
        print(f"    {step['step']}. {step['action']} ({step['software']})")
    
    print("\n" + "=" * 60)
    print("✅ 软件适配器扩展演示完成！")
    print("💡 提示: 这是演示模式，实际使用时将连接真实的软件接口")
    print("=" * 60)


if __name__ == "__main__":
    demo_software_adapter_management()