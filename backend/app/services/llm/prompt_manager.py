#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提示词管理器
提供各类任务的提示词模板
"""

from typing import Dict, Optional
import json

class PromptManager:
    """提示词管理器"""
    
    DEFAULT_PROMPTS = {
        "intent_classification": """你是一个意图分类专家。根据用户输入，判断用户的意图。

可能的意图：
- parameter_extraction: 从文档中提取参数
- simulation_run: 运行化工模拟
- report_generation: 生成报告
- document_translation: 翻译文档
- software_operation: 操作软件
- general_chat: 一般对话

用户输入：{user_input}

请直接返回意图名称，不要有其他内容：""",

        "parameter_extraction": """你是一个化工参数提取专家。从以下文本中提取参数。

可识别的参数类型:
{parameter_types}

输入文本:
{input_text}

请以JSON格式返回提取的参数，格式如下：
{{
    "parameters": [
        {{"name": "参数名", "value": "参数值", "unit": "单位", "source": "来源"}}
    ],
    "confidence": 0.0-1.0之间的置信度
}}""",

        "translation_professional": """你是一个专业的化工领域翻译专家。请将以下文本翻译成{target_lang}。
要求：
1. 保持专业术语的准确性
2. 译文流畅自然
3. 保持原文格式
4. 如果遇到不确定的术语，保留英文并在括号中说明

原文：
{text}

译文：""",

        "translation_technical": """你是一个技术文档翻译专家。请将以下技术文档翻译成{target_lang}。
要求：
1. 准确翻译技术术语
2. 保持代码和公式格式
3. 使用准确的技术用语
4. 如果遇到不确定的术语，保留英文

原文：
{text}

译文：""",

        "report_parameter_summary": """你是一个化工技术文档专家。请根据以下解析的文档内容，生成一份参数汇总报告。

要求：
1. 提取并汇总所有关键参数
2. 按类别分组展示
3. 提供参数单位换算（如需要）
4. 使用表格清晰展示

原始数据：
{data}

参数汇总报告：""",

        "report_simulation_result": """你是一个化工模拟专家。请根据以下模拟结果数据，生成一份详细的模拟结果报告。

要求：
1. 总结模拟的关键结果
2. 分析数据趋势
3. 指出需要注意的问题
4. 提供专业建议

模拟数据：
{data}

模拟结果报告：""",

        "report_data_comparison": """你是一个数据分析专家。请根据以下数据，生成一份数据对比报告。

要求：
1. 对比各项数据的差异
2. 使用表格和图表展示对比结果
3. 分析差异原因
4. 提供改进建议

对比数据：
{data}

数据对比报告：""",

        "parameter_mapping": """你是一个化工软件参数映射专家。请将以下从{source_software}软件的参数映射到{target_software}软件。

源参数：
{parameters}

请返回映射后的参数，使用{target_software}软件的参数名称，格式如下：
{{
    "mapped_parameters": [
        {{"source_name": "原参数名", "target_name": "目标参数名", "value": "参数值", "notes": "备注"}}
    ],
    "unmapped": ["无法映射的参数列表"],
    "confidence": 映射置信度
}}""",

        "execution_plan": """你是一个任务规划专家。请根据以下信息生成执行计划。

任务类型：{task_type}
提取的参数：{parameters}
目标软件：{target_software}

请生成执行计划，格式如下：
{{
    "steps": [
        {{"id": "step_1", "tool": "工具名称", "parameters": {{}}, "dependencies": []}}
    ],
    "estimated_time": "预计时间",
    "possible_issues": ["可能的问题"]
}}""",

        "dwsim_intent_classification": """你是一个化工流程模拟专家。根据用户输入，判断用户想要在DWSIM中执行的操作。

可能的意图：
- dwsim_create_flowsheet: 创建新的流程图
- dwsim_run_simulation: 运行仿真计算
- dwsim_sensitivity_analysis: 执行灵敏度分析
- dwsim_optimization: 执行参数优化
- dwsim_add_equipment: 添加设备（泵、压缩机、加热器、冷却器、阀门、混合器、反应器、精馏塔等）
- dwsim_add_stream: 添加物料流
- dwsim_set_parameters: 设置参数（温度、压力、流量、组成等）
- dwsim_get_results: 获取仿真结果
- dwsim_load_flowsheet: 加载已有流程图
- dwsim_save_flowsheet: 保存流程图
- dwsim_connect_objects: 连接设备和物料流
- general_chat: 一般对话或无法识别的操作

用户输入：{user_input}

请直接返回意图名称，不要有其他内容：""",

        "dwsim_parameter_extraction": """你是一个化工流程模拟专家。从用户输入中提取DWSIM仿真所需的参数。

可识别的参数类型：
- compounds: 化合物名称列表，如 ['Water', 'Ethanol', 'Methanol']
- property_package: 物性包名称，可选值: Peng-Robinson (PR), Soave-Redlich-Kwong (SRK), NRTL, UNIQUAC, UNIFAC, Wilson, CoolProp
- temperature: 温度，单位K
- pressure: 压力，单位Pa
- molar_flow: 摩尔流量，单位kmol/h
- mass_flow: 质量流量，单位kg/h
- composition: 摩尔组成，如 [0.5, 0.3, 0.2]
- equipment_type: 设备类型，可选值: pump, compressor, heater, cooler, valve, mixer, splitter, heat_exchanger, reactor, distillation_column, flash_drum, tank
- equipment_name: 设备名称
- stream_name: 物料流名称
- variable_object: 灵敏度分析变量对象
- variable_property: 灵敏度分析变量属性
- variable_range: 变量变化范围
- objective_object: 目标对象
- objective_property: 目标属性
- bounds: 优化边界
- objectives: 优化目标列表
- file_path: 文件路径

用户输入：
{input_text}

请以JSON格式返回提取的参数，格式如下：
{{
    "parameters": {{
        "参数名": "参数值"
    }},
    "confidence": 0.0-1.0之间的置信度
}}""",

        "dwsim_equipment_mapping": """你是一个化工流程模拟专家。根据用户描述，确定要添加的设备类型和参数。

设备类型映射：
- 泵/pump -> pump
- 压缩机/compressor -> compressor
- 加热器/加热炉/heater -> heater
- 冷却器/冷凝器/cooler -> cooler
- 阀门/调节阀/valve -> valve
- 混合器/mixer -> mixer
- 分流器/splitter -> splitter
- 换热器/热交换器/heat_exchanger -> heat_exchanger
- 反应器/reactor -> reactor
- 精馏塔/蒸馏塔/distillation_column -> distillation_column
- 闪蒸罐/flash_drum -> flash_drum
- 储罐/罐/tank -> tank

用户输入：
{input_text}

请返回设备信息，格式如下：
{{
    "equipment_type": "设备类型",
    "equipment_name": "设备名称",
    "parameters": {{
        "参数名": "参数值"
    }}
}}""",

        "dwsim_task_planning": """你是一个化工流程模拟专家。根据用户需求，规划DWSIM仿真任务步骤。

可用操作：
- connect: 连接DWSIM
- create_flowsheet: 创建流程图
- load_flowsheet: 加载流程图
- add_compounds: 添加化合物
- create_and_add_property_package: 创建物性包
- add_material_stream: 添加物料流
- add_pump/compressor/heater/cooler/valve/mixer/splitter/heat_exchanger/reactor/distillation_column/flash_drum/tank: 添加设备
- connect_objects: 连接对象
- set_object_property: 设置属性
- run_simulation: 运行仿真
- get_results: 获取结果
- sensitivity_analysis: 灵敏度分析
- optimize_single_parameter: 单参数优化
- multi_objective_optimization: 多目标优化
- save_flowsheet: 保存流程图

用户请求：{user_request}

已提取参数：{extracted_params}

请生成执行计划，格式如下：
{{
    "task_type": "任务类型",
    "required_skills": ["dwsim"],
    "confidence": 0.95,
    "estimated_time": 60.0,
    "steps": [
        {{
            "step_id": 1,
            "skill_name": "dwsim",
            "action": "操作名称",
            "parameters": {{参数键值对}},
            "depends_on": [],
            "description": "步骤描述"
        }}
    ]
}}"""
    }
    
    def __init__(self):
        self.custom_prompts = {}
        
    def get_prompt(self, key: str, **kwargs) -> str:
        """获取提示词"""
        template = self.custom_prompts.get(key) or self.DEFAULT_PROMPTS.get(key, "")
        if kwargs:
            try:
                return template.format(**kwargs)
            except KeyError as e:
                return template
        return template
    
    def update_prompt(self, key: str, template: str):
        """更新提示词"""
        self.custom_prompts[key] = template
        
    def reset_prompt(self, key: str):
        """重置提示词到默认"""
        if key in self.custom_prompts:
            del self.custom_prompts[key]
            
    def get_all_prompts(self) -> Dict[str, str]:
        """获取所有提示词"""
        return {**self.DEFAULT_PROMPTS, **self.custom_prompts}

prompt_manager = PromptManager()
