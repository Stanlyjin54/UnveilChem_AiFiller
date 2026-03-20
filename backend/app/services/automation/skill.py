#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill 标准化模型
定义化工软件自动化技能的标准结构
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from enum import Enum


class SkillCategory(Enum):
    """Skill 分类"""
    SIMULATION = "simulation"      # 流程模拟
    CAD = "cad"                   # CAD设计
    OFFICE = "office"             # 办公软件
    CHEMICAL = "chemical"         # 化学计算
    DATA = "data"                 # 数据处理
    GENERAL = "general"           # 通用


class SkillAction(BaseModel):
    """Skill 操作定义"""
    name: str = Field(..., description="操作名称")
    description: str = Field(..., description="操作描述")
    required_params: List[str] = Field(default_factory=list, description="必需参数")
    optional_params: List[str] = Field(default_factory=list, description="可选参数")
    example: Optional[str] = Field(None, description="使用示例")


class Skill(BaseModel):
    """Skill 标准化模型"""
    name: str = Field(..., description="技能标识 (唯一)")
    display_name: str = Field(..., description="显示名称")
    keywords: List[str] = Field(default_factory=list, description="激活关键词")
    description: str = Field(..., description="能力描述")
    category: SkillCategory = Field(SkillCategory.SIMULATION, description="分类")
    software_type: str = Field(..., description="依赖软件类型")
    icon: Optional[str] = Field(None, description="图标")
    actions: List[SkillAction] = Field(default_factory=list, description="支持的操作")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="参数定义")
    is_enabled: bool = Field(True, description="是否启用")
    version: str = Field("1.0.0", description="版本号")
    documentation: Optional[str] = Field(None, description="文档链接")


class SkillMatchResult(BaseModel):
    """Skill 匹配结果"""
    skill: Skill
    confidence: float = Field(..., description="匹配置信度 (0-1)")
    matched_keywords: List[str] = Field(default_factory=list, description="匹配的关键词")
    suggested_action: Optional[str] = Field(None, description="建议的操作")


class SkillRegistry:
    """Skill 注册表 - 管理所有可用 Skills"""

    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._register_default_skills()

    def _register_default_skills(self):
        """注册默认 Skills"""
        default_skills = [
            # DWSIM Skill - 完整版
            Skill(
                name="dwsim",
                display_name="DWSIM",
                keywords=[
                    "dwsim", "模拟", "流程模拟", "化工仿真", "精馏", "吸收", "反应", "换热", "加热", "冷却",
                    "泵", "压缩机", "阀门", "混合器", "分流器", "反应器", "闪蒸", "塔", "灵敏度分析", "优化"
                ],
                description="DWSIM 化工流程模拟软件自动化（COM/pythonnet 接口），支持流程图创建、仿真计算、灵敏度分析和优化",
                category=SkillCategory.SIMULATION,
                software_type="dwsim",
                version="2.0.0",
                actions=[
                    # 连接管理
                    SkillAction(
                        name="connect",
                        description="连接到 DWSIM Automation3 接口",
                        required_params=[],
                        optional_params=["dwsim_path"],
                        example="connect(dwsim_path='C:\\\\Users\\\\user\\\\AppData\\\\Local\\\\DWSIM')"
                    ),
                    SkillAction(
                        name="disconnect",
                        description="断开与 DWSIM 的连接并释放资源",
                        required_params=[],
                        optional_params=[]
                    ),
                    SkillAction(
                        name="get_version",
                        description="获取 DWSIM 版本信息",
                        required_params=[],
                        optional_params=[]
                    ),
                    # 流程图管理
                    SkillAction(
                        name="create_flowsheet",
                        description="创建新的流程图",
                        required_params=[],
                        optional_params=["name"]
                    ),
                    SkillAction(
                        name="load_flowsheet",
                        description="从文件加载流程图",
                        required_params=["file_path"],
                        optional_params=[]
                    ),
                    SkillAction(
                        name="save_flowsheet",
                        description="保存流程图到文件",
                        required_params=["file_path"],
                        optional_params=["flowsheet"]
                    ),
                    SkillAction(
                        name="auto_layout",
                        description="自动排列流程图中的对象",
                        required_params=[],
                        optional_params=["flowsheet"]
                    ),
                    # 化合物管理
                    SkillAction(
                        name="add_compound",
                        description="添加化合物到流程图",
                        required_params=["compound_name"],
                        optional_params=["flowsheet"],
                        example="add_compound(compound_name='Water')"
                    ),
                    SkillAction(
                        name="add_compounds",
                        description="批量添加化合物",
                        required_params=["compound_names"],
                        optional_params=["flowsheet"],
                        example="add_compounds(compound_names=['Water', 'Ethanol', 'Methanol'])"
                    ),
                    SkillAction(
                        name="get_available_compounds",
                        description="获取所有可用化合物列表",
                        required_params=[],
                        optional_params=[]
                    ),
                    # 物性包管理
                    SkillAction(
                        name="create_property_package",
                        description="创建物性包",
                        required_params=["package_name"],
                        optional_params=["flowsheet"],
                        example="create_property_package(package_name='Peng-Robinson (PR)')"
                    ),
                    SkillAction(
                        name="add_property_package",
                        description="添加物性包到流程图",
                        required_params=["package"],
                        optional_params=["flowsheet"]
                    ),
                    SkillAction(
                        name="create_and_add_property_package",
                        description="创建并添加物性包（一步完成）",
                        required_params=["package_name"],
                        optional_params=["flowsheet"],
                        example="create_and_add_property_package(package_name='NRTL')"
                    ),
                    SkillAction(
                        name="get_available_property_packages",
                        description="获取所有可用物性包列表",
                        required_params=[],
                        optional_params=[]
                    ),
                    # 对象管理 - 物料流
                    SkillAction(
                        name="add_material_stream",
                        description="添加物料流",
                        required_params=["name"],
                        optional_params=["x", "y", "temperature", "pressure", "molar_flow", "composition"],
                        example="add_material_stream(name='Feed', temperature=298.15, pressure=101325)"
                    ),
                    # 对象管理 - 单元操作
                    SkillAction(
                        name="add_pump",
                        description="添加泵",
                        required_params=["name"],
                        optional_params=["x", "y", "parameters"]
                    ),
                    SkillAction(
                        name="add_compressor",
                        description="添加压缩机",
                        required_params=["name"],
                        optional_params=["x", "y", "parameters"]
                    ),
                    SkillAction(
                        name="add_heater",
                        description="添加加热器",
                        required_params=["name"],
                        optional_params=["x", "y", "parameters"]
                    ),
                    SkillAction(
                        name="add_cooler",
                        description="添加冷却器",
                        required_params=["name"],
                        optional_params=["x", "y", "parameters"]
                    ),
                    SkillAction(
                        name="add_valve",
                        description="添加阀门",
                        required_params=["name"],
                        optional_params=["x", "y", "parameters"]
                    ),
                    SkillAction(
                        name="add_mixer",
                        description="添加混合器",
                        required_params=["name"],
                        optional_params=["x", "y", "parameters"]
                    ),
                    SkillAction(
                        name="add_splitter",
                        description="添加分流器",
                        required_params=["name"],
                        optional_params=["x", "y", "parameters"]
                    ),
                    SkillAction(
                        name="add_heat_exchanger",
                        description="添加换热器",
                        required_params=["name"],
                        optional_params=["x", "y", "parameters"]
                    ),
                    SkillAction(
                        name="add_reactor",
                        description="添加反应器",
                        required_params=["name"],
                        optional_params=["x", "y", "reactor_type", "parameters"]
                    ),
                    SkillAction(
                        name="add_distillation_column",
                        description="添加精馏塔",
                        required_params=["name"],
                        optional_params=["x", "y", "stages", "parameters"]
                    ),
                    SkillAction(
                        name="add_flash_drum",
                        description="添加闪蒸罐",
                        required_params=["name"],
                        optional_params=["x", "y", "parameters"]
                    ),
                    SkillAction(
                        name="add_tank",
                        description="添加储罐",
                        required_params=["name"],
                        optional_params=["x", "y", "parameters"]
                    ),
                    SkillAction(
                        name="add_object",
                        description="添加任意类型对象（通用方法）",
                        required_params=["object_type", "name"],
                        optional_params=["x", "y", "parameters"],
                        example="add_object(object_type=0, name='Feed')  # 0=MaterialStream"
                    ),
                    # 连接管理
                    SkillAction(
                        name="connect_objects",
                        description="连接两个对象",
                        required_params=["from_object", "to_object"],
                        optional_params=["from_port", "to_port"],
                        example="connect_objects(from_object='Feed', to_object='Pump')"
                    ),
                    SkillAction(
                        name="disconnect_objects",
                        description="断开两个对象的连接",
                        required_params=["from_object", "to_object"],
                        optional_params=[]
                    ),
                    # 参数设置
                    SkillAction(
                        name="set_parameters",
                        description="设置仿真参数（化合物、物性包、物料流、设备）",
                        required_params=[],
                        optional_params=["compounds", "property_package", "streams", "equipment", "connections"]
                    ),
                    SkillAction(
                        name="set_object_property",
                        description="设置对象属性值",
                        required_params=["object_name", "property_name", "value"],
                        optional_params=[],
                        example="set_object_property(object_name='Feed', property_name='Temperature', value=350)"
                    ),
                    SkillAction(
                        name="get_object_property",
                        description="获取对象属性值",
                        required_params=["object_name", "property_name"],
                        optional_params=[]
                    ),
                    # 仿真计算
                    SkillAction(
                        name="run_simulation",
                        description="运行仿真计算",
                        required_params=[],
                        optional_params=["flowsheet"]
                    ),
                    SkillAction(
                        name="check_status",
                        description="检查计算状态",
                        required_params=[],
                        optional_params=["flowsheet"]
                    ),
                    SkillAction(
                        name="request_calculation",
                        description="请求计算（异步）",
                        required_params=[],
                        optional_params=["flowsheet"]
                    ),
                    # 结果获取
                    SkillAction(
                        name="get_results",
                        description="获取仿真结果",
                        required_params=[],
                        optional_params=["stream_name", "equipment_name"]
                    ),
                    SkillAction(
                        name="get_stream_results",
                        description="获取物料流结果",
                        required_params=["stream_name"],
                        optional_params=["properties"],
                        example="get_stream_results(stream_name='Product', properties=['Temperature', 'Pressure', 'MolarFlow'])"
                    ),
                    SkillAction(
                        name="get_equipment_results",
                        description="获取设备结果",
                        required_params=["equipment_name"],
                        optional_params=["properties"]
                    ),
                    # 反应管理
                    SkillAction(
                        name="create_equilibrium_reaction",
                        description="创建平衡反应",
                        required_params=["name"],
                        optional_params=["reactants", "products", "equilibrium_constant"]
                    ),
                    SkillAction(
                        name="create_kinetic_reaction",
                        description="创建动力学反应",
                        required_params=["name"],
                        optional_params=["reactants", "products", "rate_expression"]
                    ),
                    SkillAction(
                        name="create_conversion_reaction",
                        description="创建转化反应",
                        required_params=["name"],
                        optional_params=["reactants", "products", "conversion"]
                    ),
                    SkillAction(
                        name="create_reaction_set",
                        description="创建反应集",
                        required_params=["name"],
                        optional_params=["reactions"]
                    ),
                    SkillAction(
                        name="add_reaction",
                        description="添加反应到流程图",
                        required_params=["reaction"],
                        optional_params=["flowsheet"]
                    ),
                    SkillAction(
                        name="add_reaction_to_set",
                        description="添加反应到反应集",
                        required_params=["reaction", "reaction_set"],
                        optional_params=[]
                    ),
                    # 高级功能
                    SkillAction(
                        name="sensitivity_analysis",
                        description="执行灵敏度分析",
                        required_params=["variable_object", "variable_property", "variable_range", "objective_object", "objective_property"],
                        optional_params=["flowsheet"],
                        example="sensitivity_analysis(variable_object='Feed', variable_property='Temperature', variable_range=[300, 350, 400], objective_object='Product', objective_property='MolarFlow')"
                    ),
                    SkillAction(
                        name="optimize_single_parameter",
                        description="单参数优化",
                        required_params=["param_object", "param_property", "objective_object", "objective_property", "bounds"],
                        optional_params=["flowsheet", "method"]
                    ),
                    SkillAction(
                        name="multi_objective_optimization",
                        description="多目标优化（使用 NSGA-II）",
                        required_params=["objectives", "bounds"],
                        optional_params=["flowsheet", "population_size", "generations"]
                    ),
                ],
                parameters={
                    # 基本参数
                    "compounds": {"type": "list", "description": "化合物列表，如 ['Water', 'Ethanol']"},
                    "property_package": {"type": "string", "description": "物性包名称", "options": ["Peng-Robinson (PR)", "Soave-Redlich-Kwong (SRK)", "NRTL", "UNIQUAC", "UNIFAC", "Wilson", "CoolProp", "Steam Tables (IAPWS-IF97)"]},
                    "streams": {"type": "list", "description": "物料流列表"},
                    "equipment": {"type": "list", "description": "设备列表"},
                    "connections": {"type": "list", "description": "物流连接列表"},
                    # 物性参数
                    "temperature": {"type": "float", "unit": "K", "range": [0, 2000], "description": "温度"},
                    "pressure": {"type": "float", "unit": "Pa", "range": [0, 1e8], "description": "压力"},
                    "molar_flow": {"type": "float", "unit": "kmol/h", "range": [0, 1e6], "description": "摩尔流量"},
                    "mass_flow": {"type": "float", "unit": "kg/h", "range": [0, 1e9], "description": "质量流量"},
                    "composition": {"type": "list", "description": "摩尔组成，如 [0.5, 0.5]"},
                    # 对象类型
                    "object_type": {"type": "int", "description": "对象类型ID", "options": {"0": "MaterialStream", "1": "Pump", "2": "Compressor", "3": "Heater", "4": "Cooler", "5": "Valve", "6": "Mixer", "7": "Splitter", "8": "HeatExchanger", "9": "Reactor", "10": "DistillationColumn", "11": "AbsorptionColumn", "14": "Tank", "22": "ShortcutColumn", "23": "FlashDrum"}},
                    # 位置参数
                    "x": {"type": "int", "description": "X 坐标位置"},
                    "y": {"type": "int", "description": "Y 坐标位置"},
                    # 优化参数
                    "bounds": {"type": "list", "description": "优化边界，如 [(300, 500), (1e5, 1e6)]"},
                    "objectives": {"type": "list", "description": "目标函数列表"},
                    "population_size": {"type": "int", "description": "种群大小", "default": 100},
                    "generations": {"type": "int", "description": "迭代代数", "default": 50},
                }
            ),

            # Aspen Plus Skill
            Skill(
                name="aspen_plus",
                display_name="Aspen Plus",
                keywords=["aspen", "模拟", "流程模拟", "化工", "apewn", "plus"],
                description="Aspen Plus 化工流程模拟软件自动化",
                category=SkillCategory.SIMULATION,
                software_type="aspen_plus",
                actions=[
                    SkillAction(
                        name="connect",
                        description="连接到 Aspen Plus",
                        required_params=[],
                        optional_params=["version"]
                    ),
                    SkillAction(
                        name="open_file",
                        description="打开模拟文件",
                        required_params=["file_path"],
                        optional_params=[]
                    ),
                    SkillAction(
                        name="run",
                        description="运行模拟",
                        required_params=[],
                        optional_params=["mode"]
                    ),
                    SkillAction(
                        name="set_stream",
                        description="设置物流参数",
                        required_params=["stream_id", "composition"],
                        optional_params=["temperature", "pressure", "flow"]
                    ),
                    SkillAction(
                        name="get_results",
                        description="获取结果数据",
                        required_params=["block_id"],
                        optional_params=["stream_id"]
                    ),
                ],
                parameters={
                    "temperature": {"type": "float", "unit": "°C", "range": [-273, 2000]},
                    "pressure": {"type": "float", "unit": "bar", "range": [0, 5000]},
                    "molar_flow": {"type": "float", "unit": "kmol/h", "range": [0, 1e10]},
                    "mass_flow": {"type": "float", "unit": "kg/h", "range": [0, 1e12]},
                }
            ),

            # Excel Skill
            Skill(
                name="excel",
                display_name="Microsoft Excel",
                keywords=["excel", "表格", "数据", " spreadsheet", "xlsx", "csv"],
                description="Microsoft Excel 自动化操作",
                category=SkillCategory.OFFICE,
                software_type="excel",
                actions=[
                    SkillAction(
                        name="open",
                        description="打开 Excel 文件",
                        required_params=["file_path"],
                        optional_params=["visible"]
                    ),
                    SkillAction(
                        name="read_data",
                        description="读取数据",
                        required_params=["sheet_name", "range"],
                        optional_params=["header"]
                    ),
                    SkillAction(
                        name="write_data",
                        description="写入数据",
                        required_params=["sheet_name", "data", "start_cell"],
                        optional_params=[]
                    ),
                    SkillAction(
                        name="create_chart",
                        description="创建图表",
                        required_params=["chart_type", "data_range"],
                        optional_params=["title", "position"]
                    ),
                ],
                parameters={
                    "sheet_name": {"type": "string", "description": "工作表名称"},
                    "cell_range": {"type": "string", "description": "单元格范围，如 A1:B10"},
                }
            ),

            # AutoCAD Skill
            Skill(
                name="autocad",
                display_name="AutoCAD",
                keywords=["autocad", "cad", "绘图", "dwg", "dxf"],
                description="AutoCAD 绘图软件自动化",
                category=SkillCategory.CAD,
                software_type="autocad",
                actions=[
                    SkillAction(
                        name="open_drawing",
                        description="打开图纸",
                        required_params=["file_path"],
                        optional_params=[]
                    ),
                    SkillAction(
                        name="draw_line",
                        description="绘制直线",
                        required_params=["start_point", "end_point"],
                        optional_params=["layer", "color"]
                    ),
                    SkillAction(
                        name="draw_dimension",
                        description="添加标注",
                        required_params=["start_point", "end_point", "text"],
                        optional_params=["style"]
                    ),
                    SkillAction(
                        name="export_pdf",
                        description="导出 PDF",
                        required_params=["output_path"],
                        optional_params=["layout"]
                    ),
                ],
                parameters={
                    "point": {"type": "array", "description": "坐标点 [x, y]"},
                    "layer": {"type": "string", "description": "图层名称"},
                }
            ),

            # PRO/II Skill
            Skill(
                name="pro_ii",
                display_name="PRO/II",
                keywords=["pro/ii", "pro2", "simsci", "模拟", "流程"],
                description="PRO/II 化工流程模拟软件",
                category=SkillCategory.SIMULATION,
                software_type="pro_ii",
                actions=[
                    SkillAction(
                        name="new_case",
                        description="创建新案例",
                        required_params=[],
                        optional_params=["template"]
                    ),
                    SkillAction(
                        name="run_simulation",
                        description="运行模拟",
                        required_params=[],
                        optional_params=["convergence_tolerance"]
                    ),
                    SkillAction(
                        name="get_stream_results",
                        description="获取物流结果",
                        required_params=["stream_id"],
                        optional_params=["property"]
                    ),
                ],
                parameters={}
            ),

            # ChemCAD Skill
            Skill(
                name="chemcad",
                display_name="ChemCAD",
                keywords=["chemcad", "cc5", "cc6", "模拟"],
                description="ChemCAD 化工流程模拟软件",
                category=SkillCategory.SIMULATION,
                software_type="chemcad",
                actions=[
                    SkillAction(
                        name="load_simulation",
                        description="加载模拟文件",
                        required_params=["file_path"],
                        optional_params=[]
                    ),
                    SkillAction(
                        name="run",
                        description="运行模拟",
                        required_params=[],
                        optional_params=[]
                    ),
                ],
                parameters={}
            ),
        ]

        for skill in default_skills:
            self.register_skill(skill)

    def register_skill(self, skill: Skill):
        """注册 Skill"""
        self._skills[skill.name] = skill

    def get_skill(self, name: str) -> Optional[Skill]:
        """获取 Skill"""
        return self._skills.get(name)

    def get_all_skills(self) -> List[Skill]:
        """获取所有 Skills"""
        return list(self._skills.values())

    def get_enabled_skills(self) -> List[Skill]:
        """获取启用的 Skills"""
        return [s for s in self._skills.values() if s.is_enabled]

    def get_skills_by_category(self, category: SkillCategory) -> List[Skill]:
        """按分类获取 Skills"""
        return [s for s in self._skills.values() if s.category == category]

    def search_by_keyword(self, keyword: str) -> List[SkillMatchResult]:
        """通过关键词搜索 Skills"""
        keyword_lower = keyword.lower()
        results = []

        for skill in self.get_enabled_skills():
            matched_keywords = []
            confidence = 0.0

            for kw in skill.keywords:
                kw_lower = kw.lower()
                if kw_lower == keyword_lower:
                    confidence = 1.0
                    matched_keywords.append(kw)
                elif keyword_lower in kw_lower or kw_lower in keyword_lower:
                    confidence = max(confidence, 0.8)
                    matched_keywords.append(kw)

            if confidence > 0:
                results.append(SkillMatchResult(
                    skill=skill,
                    confidence=confidence,
                    matched_keywords=matched_keywords
                ))

        # 按置信度排序
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results

    def to_dict(self) -> List[Dict[str, Any]]:
        """转换为字典列表"""
        return [skill.model_dump() for skill in self.get_all_skills()]


# 全局实例
_skill_registry: Optional[SkillRegistry] = None


def get_skill_registry() -> SkillRegistry:
    """获取 Skill 注册表实例"""
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = SkillRegistry()
    return _skill_registry
