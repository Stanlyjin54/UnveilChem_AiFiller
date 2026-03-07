#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SolidWorks自动化适配器
通过COM接口连接SolidWorks,实现3D模型参数设置和工程图生成
"""

import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .base_adapter import SoftwareAutomationAdapter, AutomationResult, AutomationStatus
from .parameter_mapper import ParameterMapper
from .error_handler import ErrorSeverity, ErrorCategory, ErrorContext

logger = logging.getLogger(__name__)

try:
    import win32com.client
    import pythoncom
    COM_AVAILABLE = True
except ImportError:
    COM_AVAILABLE = False
    logger.warning("win32com 不可用,SolidWorks适配器功能受限")

@dataclass
class SolidWorksParameter:
    """SolidWorks参数定义"""
    name: str
    value: Any
    unit: str
    description: str
    configuration: str  # 配置名称
    feature: str  # 特征名称

class SolidWorksAdapter(SoftwareAutomationAdapter):
    """SolidWorks自动化适配器"""
    
    def __init__(self):
        super().__init__()
        self.parameter_mapper = ParameterMapper()
        self.sw_app = None  # SolidWorks应用实例
        self.active_doc = None  # 当前文档
        self.is_connected = False
        self.error_handler = None  # 错误处理器将在外部设置
        
        # SolidWorks参数映射表
        self.solidworks_parameter_map = {
            # 几何参数
            'diameter': {
                'pipe_diameter': 'D1@Sketch1',
                'vessel_diameter': 'D2@Sketch1',
                'nozzle_diameter': 'D3@Sketch1'
            },
            'length': {
                'pipe_length': 'D1@Extrude1',
                'vessel_length': 'D2@Extrude1',
                'flange_thickness': 'D3@Extrude1'
            },
            'width': {
                'vessel_width': 'D4@Sketch1',
                'support_width': 'D5@Sketch1'
            },
            'height': {
                'vessel_height': 'D6@Sketch1',
                'support_height': 'D7@Sketch1'
            },
            # 角度参数
            'angle': {
                'cone_angle': 'D1@Sketch2',
                'nozzle_angle': 'D2@Sketch2'
            },
            # 材料参数
            'material': {
                'pipe_material': 'Material@Part',
                'vessel_material': 'Material@Part'
            },
            # 质量参数
            'mass': {
                'part_mass': 'SW-Mass@Properties',
                'volume': 'SW-Volume@Properties'
            },
            # 工程图参数
            'drawing': {
                'sheet_size': 'SheetFormatSize',
                'scale': 'SheetScale'
            }
        }
    
    def connect(self, **kwargs) -> bool:
        """连接到SolidWorks"""
        try:
            if not COM_AVAILABLE:
                raise RuntimeError("COM接口不可用,无法连接SolidWorks")
            
            logger.info("正在连接到SolidWorks...")
            
            # 初始化COM
            pythoncom.CoInitialize()
            
            # 创建SolidWorks应用实例
            self.sw_app = win32com.client.Dispatch("SldWorks.Application")
            
            # 验证连接
            if self.sw_app is None:
                raise RuntimeError("无法创建SolidWorks应用实例")
            
            # 设置可见性
            self.sw_app.Visible = True
            
            self.is_connected = True
            logger.info("成功连接到SolidWorks")
            return True
            
        except Exception as e:
            logger.error(f"连接SolidWorks失败: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> bool:
        """断开SolidWorks连接"""
        try:
            if self.sw_app:
                # 关闭当前文档
                if self.active_doc:
                    try:
                        self.active_doc.Close(False)  # False表示不保存
                    except:
                        pass
                
                # 退出SolidWorks
                try:
                    self.sw_app.ExitApp()
                except:
                    pass
                
                self.sw_app = None
                self.active_doc = None
            
            self.is_connected = False
            logger.info("已断开SolidWorks连接")
            return True
            
        except Exception as e:
            logger.error(f"断开SolidWorks连接失败: {e}")
            return False
    
    def open_document(self, file_path: str) -> bool:
        """打开文档"""
        try:
            if not self.is_connected:
                raise RuntimeError("未连接到SolidWorks")
            
            logger.info(f"正在打开SolidWorks文档: {file_path}")
            
            # 打开文档
            self.active_doc = self.sw_app.OpenDoc(file_path, 1)  # 1 = Part document
            
            if self.active_doc is None:
                raise RuntimeError("无法打开SolidWorks文档")
            
            logger.info("成功打开SolidWorks文档")
            return True
            
        except Exception as e:
            logger.error(f"打开SolidWorks文档失败: {e}")
            return False
    
    def create_new_part(self, template_path: str = None) -> bool:
        """创建新零件"""
        try:
            if not self.is_connected:
                raise RuntimeError("未连接到SolidWorks")
            
            logger.info("正在创建新SolidWorks零件...")
            
            # 创建新零件
            if template_path:
                self.active_doc = self.sw_app.NewDocument(template_path, 0, 0, 0)
            else:
                # 使用默认模板
                self.active_doc = self.sw_app.NewPart()
            
            if self.active_doc is None:
                raise RuntimeError("无法创建新SolidWorks零件")
            
            logger.info("成功创建新SolidWorks零件")
            return True
            
        except Exception as e:
            logger.error(f"创建新SolidWorks零件失败: {e}")
            return False
    
    def save_document(self, file_path: str) -> bool:
        """保存文档"""
        try:
            if not self.active_doc:
                raise RuntimeError("没有打开的文档")
            
            logger.info(f"正在保存SolidWorks文档: {file_path}")
            
            # 保存文档
            self.active_doc.SaveAs(file_path)
            
            logger.info("成功保存SolidWorks文档")
            return True
            
        except Exception as e:
            logger.error(f"保存SolidWorks文档失败: {e}")
            return False
    
    def set_parameter(self, param_name: str, value: Any, configuration: str = None) -> bool:
        """设置参数"""
        try:
            if not self.active_doc:
                raise RuntimeError("没有打开的文档")
            
            logger.info(f"正在设置SolidWorks参数: {param_name} = {value}")
            
            # 获取参数管理器
            param_mgr = self.active_doc.ParameterManager
            
            if not param_mgr:
                raise RuntimeError("无法获取参数管理器")
            
            # 设置参数
            if configuration:
                # 在指定配置中设置参数
                config_mgr = self.active_doc.ConfigurationManager
                config = config_mgr.ConfigurationByName(configuration)
                if config:
                    param = config.Parameter(param_name)
                    if param:
                        param.Value = value
                    else:
                        raise ValueError(f"参数不存在: {param_name}")
                else:
                    raise ValueError(f"配置不存在: {configuration}")
            else:
                # 在当前配置中设置参数
                param = param_mgr.Parameter(param_name)
                if param:
                    param.Value = value
                else:
                    raise ValueError(f"参数不存在: {param_name}")
            
            # 重建模型
            self.active_doc.EditRebuild3()
            
            logger.info(f"成功设置SolidWorks参数: {param_name}")
            return True
            
        except Exception as e:
            logger.error(f"设置SolidWorks参数失败: {e}")
            return False
    
    def get_parameter(self, param_name: str, configuration: str = None) -> Optional[Any]:
        """获取参数值"""
        try:
            if not self.active_doc:
                return None
            
            # 获取参数管理器
            param_mgr = self.active_doc.ParameterManager
            
            if not param_mgr:
                return None
            
            # 获取参数
            if configuration:
                config_mgr = self.active_doc.ConfigurationManager
                config = config_mgr.ConfigurationByName(configuration)
                if config:
                    param = config.Parameter(param_name)
                    if param:
                        return param.Value
            else:
                param = param_mgr.Parameter(param_name)
                if param:
                    return param.Value
            
            return None
            
        except Exception as e:
            logger.error(f"获取SolidWorks参数失败: {e}")
            return None
    
    def create_drawing(self, part_path: str, template_path: str = None) -> bool:
        """创建工程图"""
        try:
            if not self.is_connected:
                raise RuntimeError("未连接到SolidWorks")
            
            logger.info(f"正在创建SolidWorks工程图: {part_path}")
            
            # 创建工程图
            if template_path:
                drawing = self.sw_app.NewDocument(template_path, 3, 0, 0)  # 3 = Drawing document
            else:
                drawing = self.sw_app.NewDrawing()
            
            if drawing is None:
                raise RuntimeError("无法创建SolidWorks工程图")
            
            # 插入模型视图
            model_view = drawing.CreateDrawViewFromModelView(part_path, "*前视", 0, 0, 0)
            
            if model_view is None:
                logger.warning("无法自动插入模型视图")
            
            logger.info("成功创建SolidWorks工程图")
            return True
            
        except Exception as e:
            logger.error(f"创建SolidWorks工程图失败: {e}")
            return False
    
    def update_mass_properties(self) -> Optional[Dict[str, Any]]:
        """更新质量属性"""
        try:
            if not self.active_doc:
                return None
            
            # 获取质量属性
            mass_props = self.active_doc.Extension.GetMassProperties2(1, None, None)
            
            if mass_props is None:
                return None
            
            # 提取质量属性信息
            properties = {
                'mass': mass_props[0],  # 质量 (kg)
                'volume': mass_props[1],  # 体积 (m³)
                'surface_area': mass_props[2],  # 表面积 (m²)
                'center_of_mass': mass_props[3:6],  # 质心坐标
                'center_of_volume': mass_props[6:9],  # 体积中心坐标
                'moments_of_inertia': mass_props[9:18],  # 惯性矩
                'products_of_inertia': mass_props[18:24]  # 惯性积
            }
            
            logger.info("成功更新SolidWorks质量属性")
            return properties
            
        except Exception as e:
            logger.error(f"更新SolidWorks质量属性失败: {e}")
            return None
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, bool]:
        """验证参数"""
        validation_results = {}
        
        for param_name, param_value in parameters.items():
            try:
                # 查找参数映射
                mapped_param = self._find_parameter_mapping(param_name)
                
                if not mapped_param:
                    validation_results[param_name] = False
                    logger.warning(f"未找到参数映射: {param_name}")
                    continue
                
                # 验证参数类型和范围
                is_valid = self._validate_single_parameter(mapped_param, param_value)
                validation_results[param_name] = is_valid
                
                if not is_valid:
                    logger.warning(f"参数验证失败: {param_name} = {param_value}")
                
            except Exception as e:
                validation_results[param_name] = False
                logger.error(f"验证参数 {param_name} 时出错: {e}")
        
        return validation_results
    
    def _find_parameter_mapping(self, param_name: str) -> Optional[str]:
        """查找参数映射"""
        # 首先尝试直接映射
        for category, mappings in self.solidworks_parameter_map.items():
            if param_name in mappings:
                return mappings[param_name]
        
        # 使用参数映射器进行智能映射
        mapped_params = self.parameter_mapper.map_parameters(
            {param_name: None}, "solidworks"
        )
        
        if mapped_params and param_name in mapped_params:
            return mapped_params[param_name]
        
        return None
    
    def _validate_single_parameter(self, param_path: str, value: Any) -> bool:
        """验证单个参数"""
        try:
            # 基于参数类型的验证规则
            if 'diameter' in param_path.lower():
                # 直径范围验证 (mm)
                return 1 <= float(value) <= 5000
            elif 'length' in param_path.lower() or 'height' in param_path.lower():
                # 长度/高度范围验证 (mm)
                return 1 <= float(value) <= 10000
            elif 'width' in param_path.lower():
                # 宽度范围验证 (mm)
                return 1 <= float(value) <= 5000
            elif 'angle' in param_path.lower():
                # 角度范围验证 (度)
                return 0 <= float(value) <= 360
            elif 'thickness' in param_path.lower():
                # 厚度范围验证 (mm)
                return 0.1 <= float(value) <= 100
            elif 'material' in param_path.lower():
                # 材料名称验证
                return isinstance(value, str) and len(value.strip()) > 0
            elif 'mass' in param_path.lower():
                # 质量验证 (kg)
                return 0.001 <= float(value) <= 10000
            elif 'volume' in param_path.lower():
                # 体积验证 (m³)
                return 1e-6 <= float(value) <= 1000
            else:
                # 默认验证通过
                return True
                
        except (ValueError, TypeError):
            return False
    
    def get_software_info(self) -> Dict[str, Any]:
        """获取软件信息"""
        try:
            if not self.is_connected:
                return {
                    "name": "SolidWorks",
                    "version": "Unknown",
                    "connected": False,
                    "document_loaded": False
                }
            
            # 获取版本信息
            version = getattr(self.sw_app, 'RevisionNumber', 'Unknown')
            
            # 获取文档信息
            doc_info = {}
            if self.active_doc:
                doc_info = {
                    "document_type": self.active_doc.GetType(),
                    "document_path": self.active_doc.GetPathName(),
                    "needs_rebuild": self.active_doc.NeedsRebuild(),
                    "is_modified": self.active_doc.IsDirty()
                }
            
            return {
                "name": "SolidWorks",
                "version": version,
                "connected": True,
                "document_loaded": self.active_doc is not None,
                "document_info": doc_info,
                "visible": getattr(self.sw_app, 'Visible', False)
            }
            
        except Exception as e:
            logger.error(f"获取SolidWorks信息失败: {e}")
            return {
                "name": "SolidWorks",
                "version": "Unknown",
                "connected": self.is_connected,
                "document_loaded": self.active_doc is not None,
                "error": str(e)
            }
    
    def _handle_error(self, error: Exception, context: str = None) -> None:
        """处理错误"""
        logger.error(f"SolidWorks操作失败: {error}")
        if context:
            logger.error(f"上下文: {context}")

        # 构建错误上下文
        error_context = ErrorContext(
            adapter_name="solidworks",
            operation=context or "unknown_operation",
            parameters={"error": str(error)}
        )

        # 使用错误处理系统
        if hasattr(self, 'error_handler') and self.error_handler:
            self.error_handler.handle_error(
                error,
                context=error_context,
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.EXECUTION
            )

    def execute_automation(self, parameters: Dict[str, Any]) -> AutomationResult:
        """执行自动化流程"""
        start_time = time.time()

        try:
            logger.info("开始执行SolidWorks自动化流程")

            # 验证参数
            validation_results = self.validate_parameters(parameters)
            if not all(validation_results.values()):
                invalid_params = [k for k, v in validation_results.items() if not v]
                raise ValueError(f"参数验证失败: {invalid_params}")

            # 参数映射
            mapped_parameters = self.parameter_mapper.map_parameters(
                parameters, "solidworks"
            )

            if not mapped_parameters:
                raise ValueError("参数映射失败")

            # 设置参数
            parameters_set = {}
            for param_name, param_value in mapped_parameters.items():
                # 查找SolidWorks参数名称
                param_sw_name = self._find_parameter_mapping(param_name)

                if param_sw_name:
                    if self.set_parameter(param_sw_name, param_value):
                        parameters_set[param_name] = param_value
                        logger.info(f"设置参数成功: {param_name} = {param_value}")
                    else:
                        logger.warning(f"设置参数失败: {param_name}")

            # 更新质量属性
            mass_properties = self.update_mass_properties()
            if mass_properties:
                parameters_set['mass_properties'] = mass_properties
                logger.info("质量属性已更新")

            execution_time = time.time() - start_time

            return AutomationResult(
                success=True,
                status=AutomationStatus.COMPLETED,
                message="SolidWorks自动化执行成功",
                parameters_set=parameters_set,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self._handle_error(e, context="execute_automation")

            return AutomationResult(
                success=False,
                status=AutomationStatus.FAILED,
                message=f"SolidWorks自动化执行失败: {str(e)}",
                parameters_set={},
                execution_time=execution_time,
                error_details=str(e)
            )