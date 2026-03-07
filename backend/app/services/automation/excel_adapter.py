#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel 自动化适配器
通过 COM 接口与 Excel 进行交互，用于数据导出和报告生成
"""

import win32com.client
import pythoncom
import logging
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import os

from .base_adapter import SoftwareAutomationAdapter, AutomationResult, AutomationStatus, SoftwareInfo

logger = logging.getLogger(__name__)

class ExcelAdapter(SoftwareAutomationAdapter):
    """Excel 自动化适配器"""
    
    def __init__(self, version: str = "2019"):
        super().__init__("Excel", version)
        self.excel_app = None
        self.workbook = None
        self.worksheet = None
        self.connection_timeout = 30
        
    def connect(self) -> bool:
        """连接 Excel"""
        try:
            logger.info("正在连接 Excel...")
            
            # 初始化 COM
            pythoncom.CoInitialize()
            
            # 尝试连接到正在运行的 Excel 实例
            try:
                self.excel_app = win32com.client.GetActiveObject("Excel.Application")
                logger.info("连接到正在运行的 Excel 实例")
            except:
                # 如果没有运行的实例，创建新的实例
                logger.info("创建新的 Excel 实例...")
                self.excel_app = win32com.client.Dispatch("Excel.Application")
                self.excel_app.Visible = True  # 显示 Excel
                time.sleep(2)  # 等待启动
            
            logger.info("成功连接到 Excel")
            return True
            
        except Exception as e:
            logger.error(f"连接 Excel 失败: {e}")
            return False
    
    def disconnect(self) -> bool:
        """断开与 Excel 的连接"""
        try:
            if self.excel_app:
                # 保存工作簿（如果有修改）
                if self.workbook:
                    try:
                        if self.workbook.Saved == False:
                            logger.info("工作簿有未保存的更改")
                    except:
                        pass
                
                # 不强制关闭 Excel，只释放 COM 对象
                self.worksheet = None
                self.workbook = None
                self.excel_app = None
            
            # 释放 COM
            pythoncom.CoUninitialize()
            
            logger.info("已断开与 Excel 的连接")
            return True
            
        except Exception as e:
            logger.error(f"断开连接失败: {e}")
            return False
    
    def open_workbook(self, file_path: str) -> bool:
        """打开 Excel 工作簿"""
        try:
            if not self.excel_app:
                logger.error("未连接到 Excel")
                return False
            
            # 检查文件是否存在
            if not Path(file_path).exists():
                logger.error(f"工作簿文件不存在: {file_path}")
                return False
            
            logger.info(f"正在打开工作簿: {file_path}")
            
            # 打开工作簿
            self.workbook = self.excel_app.Workbooks.Open(file_path)
            
            # 获取第一个工作表
            self.worksheet = self.workbook.Worksheets(1)
            
            logger.info("工作簿打开成功")
            return True
            
        except Exception as e:
            logger.error(f"打开工作簿失败: {e}")
            return False
    
    def create_new_workbook(self, template_path: str = None) -> bool:
        """创建新工作簿"""
        try:
            if not self.excel_app:
                logger.error("未连接到 Excel")
                return False
            
            logger.info("正在创建新工作簿...")
            
            # 创建新工作簿
            if template_path and Path(template_path).exists():
                # 基于模板创建
                self.workbook = self.excel_app.Workbooks.Add(template_path)
            else:
                # 创建空白工作簿
                self.workbook = self.excel_app.Workbooks.Add()
            
            # 获取第一个工作表
            self.worksheet = self.workbook.Worksheets(1)
            
            logger.info("新工作簿创建成功")
            return True
            
        except Exception as e:
            logger.error(f"创建新工作簿失败: {e}")
            return False
    
    def save_workbook(self, save_path: str) -> bool:
        """保存工作簿"""
        try:
            if not self.workbook:
                logger.error("没有打开的工作簿")
                return False
            
            logger.info(f"正在保存工作簿到: {save_path}")
            
            # 确保目录存在
            save_dir = os.path.dirname(save_path)
            if save_dir:
                os.makedirs(save_dir, exist_ok=True)
            
            # 保存工作簿
            self.workbook.SaveAs(save_path)
            
            logger.info("工作簿保存成功")
            return True
            
        except Exception as e:
            logger.error(f"保存工作簿失败: {e}")
            return False
    
    def set_parameters(self, parameters: Dict[str, Any]) -> AutomationResult:
        """设置参数（填充 Excel 单元格）"""
        import time
        start_time = time.time()
        
        try:
            if not self.worksheet:
                logger.error("没有打开的工作表")
                return AutomationResult(
                    success=False,
                    status=AutomationStatus.FAILED,
                    message="没有打开的工作表",
                    parameters_set={},
                    execution_time=time.time() - start_time
                )
            
            logger.info(f"开始设置 {len(parameters)} 个参数...")
            
            parameters_set = {}
            row = 1  # 起始行
            
            # 创建标题行
            self.worksheet.Cells(1, 1).Value = "参数名称"
            self.worksheet.Cells(1, 2).Value = "参数值"
            self.worksheet.Cells(1, 3).Value = "单位"
            self.worksheet.Cells(1, 4).Value = "描述"
            
            # 设置标题行格式
            header_range = self.worksheet.Range("A1:D1")
            header_range.Font.Bold = True
            header_range.Interior.Color = 12611584  # 浅蓝色背景
            
            row = 2  # 数据起始行
            
            for param_name, param_data in parameters.items():
                try:
                    # 解析参数数据
                    if isinstance(param_data, dict):
                        value = param_data.get('value', '')
                        unit = param_data.get('unit', '')
                        description = param_data.get('description', '')
                    else:
                        value = param_data
                        unit = ''
                        description = ''
                    
                    # 填充单元格
                    self.worksheet.Cells(row, 1).Value = param_name  # 参数名称
                    self.worksheet.Cells(row, 2).Value = value      # 参数值
                    self.worksheet.Cells(row, 3).Value = unit       # 单位
                    self.worksheet.Cells(row, 4).Value = description  # 描述
                    
                    # 设置数值格式（如果是数值）
                    try:
                        float_value = float(value)
                        self.worksheet.Cells(row, 2).NumberFormat = "0.00"
                    except:
                        pass  # 不是数值，保持默认格式
                    
                    parameters_set[param_name] = param_data
                    logger.debug(f"设置参数成功: {param_name} = {value}")
                    
                    row += 1
                    
                except Exception as e:
                    logger.error(f"设置参数失败 {param_name}: {e}")
                    continue
            
            # 自动调整列宽
            data_range = self.worksheet.Range(f"A1:D{row-1}")
            data_range.Columns.AutoFit()
            
            # 添加边框
            data_range.Borders.LineStyle = 1  # 实线边框
            
            logger.info(f"成功设置 {len(parameters_set)} 个参数")
            
            return AutomationResult(
                success=True,
                status=AutomationStatus.COMPLETED,
                message=f"成功设置 {len(parameters_set)} 个参数",
                parameters_set=parameters_set,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"设置参数失败: {e}")
            return AutomationResult(
                success=False,
                status=AutomationStatus.FAILED,
                message=f"设置参数失败: {str(e)}",
                parameters_set={},
                execution_time=time.time() - start_time,
                error_details=str(e)
            )
    
    def create_report(self, data: Dict[str, Any], report_type: str = "parameter") -> bool:
        """创建报告"""
        try:
            if not self.worksheet:
                logger.error("没有打开的工作表")
                return False
            
            logger.info(f"正在创建 {report_type} 报告...")
            
            if report_type == "parameter":
                return self._create_parameter_report(data)
            elif report_type == "analysis":
                return self._create_analysis_report(data)
            elif report_type == "equipment":
                return self._create_equipment_report(data)
            else:
                logger.warning(f"未知的报告类型: {report_type}")
                return False
                
        except Exception as e:
            logger.error(f"创建报告失败: {e}")
            return False
    
    def _create_parameter_report(self, data: Dict[str, Any]) -> bool:
        """创建参数报告"""
        try:
            # 设置报告标题
            self.worksheet.Cells(1, 1).Value = "工艺参数报告"
            self.worksheet.Range("A1").Font.Size = 16
            self.worksheet.Range("A1").Font.Bold = True
            
            # 设置表头
            headers = ["参数名称", "数值", "单位", "来源", "置信度", "备注"]
            for col, header in enumerate(headers, 1):
                self.worksheet.Cells(3, col).Value = header
                self.worksheet.Cells(3, col).Font.Bold = True
            
            # 填充数据
            row = 4
            for param_name, param_info in data.get('parameters', {}).items():
                self.worksheet.Cells(row, 1).Value = param_name
                self.worksheet.Cells(row, 2).Value = param_info.get('value', '')
                self.worksheet.Cells(row, 3).Value = param_info.get('unit', '')
                self.worksheet.Cells(row, 4).Value = param_info.get('source', '')
                self.worksheet.Cells(row, 5).Value = param_info.get('confidence', '')
                self.worksheet.Cells(row, 6).Value = param_info.get('notes', '')
                row += 1
            
            # 格式化表格
            table_range = self.worksheet.Range(f"A3:F{row-1}")
            table_range.Borders.LineStyle = 1
            table_range.Columns.AutoFit()
            
            return True
            
        except Exception as e:
            logger.error(f"创建参数报告失败: {e}")
            return False
    
    def _create_analysis_report(self, data: Dict[str, Any]) -> bool:
        """创建分析报告"""
        try:
            # 设置报告标题
            self.worksheet.Cells(1, 1).Value = "文档分析报告"
            self.worksheet.Range("A1").Font.Size = 16
            self.worksheet.Range("A1").Font.Bold = True
            
            # 文档信息
            info_row = 3
            self.worksheet.Cells(info_row, 1).Value = "文档信息"
            self.worksheet.Cells(info_row, 1).Font.Bold = True
            
            doc_info = data.get('document_info', {})
            info_data = [
                ["文件名", doc_info.get('filename', '')],
                ["文件大小", f"{doc_info.get('size', 0)} KB"],
                ["页数", doc_info.get('pages', 0)],
                ["处理时间", doc_info.get('processing_time', '')],
            ]
            
            for i, (key, value) in enumerate(info_data):
                self.worksheet.Cells(info_row + i + 1, 1).Value = key
                self.worksheet.Cells(info_row + i + 1, 2).Value = value
            
            # 提取结果
            results_row = info_row + len(info_data) + 2
            self.worksheet.Cells(results_row, 1).Value = "提取结果"
            self.worksheet.Cells(results_row, 1).Font.Bold = True
            
            # 化学实体
            chemical_entities = data.get('chemical_entities', [])
            self.worksheet.Cells(results_row + 1, 1).Value = f"化学实体数量: {len(chemical_entities)}"
            
            # 工艺参数
            process_params = data.get('process_parameters', [])
            self.worksheet.Cells(results_row + 2, 1).Value = f"工艺参数数量: {len(process_params)}"
            
            # 自动调整列宽
            self.worksheet.Columns.AutoFit()
            
            return True
            
        except Exception as e:
            logger.error(f"创建分析报告失败: {e}")
            return False
    
    def _create_equipment_report(self, data: Dict[str, Any]) -> bool:
        """创建设备报告"""
        try:
            # 设置报告标题
            self.worksheet.Cells(1, 1).Value = "设备参数报告"
            self.worksheet.Range("A1").Font.Size = 16
            self.worksheet.Range("A1").Font.Bold = True
            
            # 设置表头
            headers = ["设备名称", "类型", "设计参数", "操作参数", "材料", "备注"]
            for col, header in enumerate(headers, 1):
                self.worksheet.Cells(3, col).Value = header
                self.worksheet.Cells(3, col).Font.Bold = True
            
            # 填充数据
            row = 4
            for equip_name, equip_info in data.get('equipment', {}).items():
                self.worksheet.Cells(row, 1).Value = equip_name
                self.worksheet.Cells(row, 2).Value = equip_info.get('type', '')
                self.worksheet.Cells(row, 3).Value = str(equip_info.get('design_params', {}))
                self.worksheet.Cells(row, 4).Value = str(equip_info.get('operating_params', {}))
                self.worksheet.Cells(row, 5).Value = equip_info.get('material', '')
                self.worksheet.Cells(row, 6).Value = equip_info.get('notes', '')
                row += 1
            
            # 格式化表格
            table_range = self.worksheet.Range(f"A3:F{row-1}")
            table_range.Borders.LineStyle = 1
            table_range.Columns.AutoFit()
            
            return True
            
        except Exception as e:
            logger.error(f"创建设备报告失败: {e}")
            return False
    
    def export_to_csv(self, data: Dict[str, Any], csv_path: str) -> bool:
        """导出到 CSV 文件"""
        try:
            if not self.workbook:
                logger.error("没有打开的工作簿")
                return False
            
            # 确保目录存在
            csv_dir = os.path.dirname(csv_path)
            if csv_dir:
                os.makedirs(csv_dir, exist_ok=True)
            
            # 另存为 CSV
            self.workbook.SaveAs(csv_path, FileFormat=6)  # 6 = xlCSV
            
            logger.info(f"成功导出到 CSV: {csv_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出到 CSV 失败: {e}")
            return False
    
    def get_software_info(self) -> SoftwareInfo:
        """获取软件信息"""
        try:
            is_running = self.excel_app is not None
            connection_status = "已连接" if is_running else "未连接"
            
            # 获取支持的参数列表
            supported_params = [
                'parameters', 'data_table', 'chart', 'report', 'csv_export'
            ]
            
            return SoftwareInfo(
                name=self.software_name,
                version=self.version,
                is_running=is_running,
                connection_status=connection_status,
                supported_parameters=supported_params
            )
            
        except Exception as e:
            logger.error(f"获取软件信息失败: {e}")
            return SoftwareInfo(
                name=self.software_name,
                version=self.version,
                is_running=False,
                connection_status="错误",
                supported_parameters=[]
            )
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证参数"""
        validated_params = {}
        
        for param_name, param_data in parameters.items():
            try:
                # 如果是字典格式，验证内部结构
                if isinstance(param_data, dict):
                    required_keys = ['value']
                    if all(key in param_data for key in required_keys):
                        validated_params[param_name] = param_data
                    else:
                        logger.warning(f"参数字典格式错误: {param_name}")
                else:
                    # 如果不是字典，转换为标准格式
                    validated_params[param_name] = {
                        'value': param_data,
                        'unit': '',
                        'description': ''
                    }
                    
            except Exception as e:
                logger.error(f"参数验证失败 {param_name}: {e}")
                continue
        
        return validated_params