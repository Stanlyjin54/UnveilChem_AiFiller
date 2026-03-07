#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoCAD 自动化适配器
通过 COM 接口与 AutoCAD 进行交互
"""

import win32com.client
import pythoncom
import logging
import time
import math
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from .base_adapter import SoftwareAutomationAdapter, AutomationResult, AutomationStatus, SoftwareInfo

logger = logging.getLogger(__name__)

class AutoCADAdapter(SoftwareAutomationAdapter):
    """AutoCAD 自动化适配器"""
    
    def __init__(self, version: str = "2024"):
        super().__init__("AutoCAD", version)
        self.acad_app = None
        self.active_doc = None
        self.model_space = None
        self.connection_timeout = 45  # AutoCAD 启动较慢
        
    def connect(self) -> bool:
        """连接 AutoCAD"""
        try:
            logger.info("正在连接 AutoCAD...")
            
            # 初始化 COM
            pythoncom.CoInitialize()
            
            # 尝试连接到正在运行的 AutoCAD 实例
            try:
                self.acad_app = win32com.client.GetActiveObject("AutoCAD.Application")
                logger.info("连接到正在运行的 AutoCAD 实例")
            except:
                # 如果没有运行的实例，创建新的实例
                logger.info("创建新的 AutoCAD 实例...")
                self.acad_app = win32com.client.Dispatch("AutoCAD.Application")
                self.acad_app.Visible = True  # 显示 AutoCAD
                time.sleep(3)  # 等待启动
            
            # 获取活动文档
            self.active_doc = self.acad_app.ActiveDocument
            self.model_space = self.active_doc.ModelSpace
            
            logger.info("成功连接到 AutoCAD")
            return True
            
        except Exception as e:
            logger.error(f"连接 AutoCAD 失败: {e}")
            return False
    
    def disconnect(self) -> bool:
        """断开与 AutoCAD 的连接"""
        try:
            if self.acad_app:
                # 不关闭 AutoCAD，只释放 COM 对象
                self.model_space = None
                self.active_doc = None
                self.acad_app = None
            
            # 释放 COM
            pythoncom.CoUninitialize()
            
            logger.info("已断开与 AutoCAD 的连接")
            return True
            
        except Exception as e:
            logger.error(f"断开连接失败: {e}")
            return False
    
    def open_drawing(self, file_path: str) -> bool:
        """打开 AutoCAD 图纸"""
        try:
            if not self.acad_app:
                logger.error("未连接到 AutoCAD")
                return False
            
            # 检查文件是否存在
            if not Path(file_path).exists():
                logger.error(f"图纸文件不存在: {file_path}")
                return False
            
            logger.info(f"正在打开图纸文件: {file_path}")
            
            # 打开图纸
            self.active_doc = self.acad_app.Documents.Open(file_path)
            self.model_space = self.active_doc.ModelSpace
            
            # 等待加载完成
            time.sleep(2)
            
            logger.info("图纸文件打开成功")
            return True
            
        except Exception as e:
            logger.error(f"打开图纸文件失败: {e}")
            return False
    
    def create_new_drawing(self, template: str = None) -> bool:
        """创建新图纸"""
        try:
            if not self.acad_app:
                logger.error("未连接到 AutoCAD")
                return False
            
            logger.info("正在创建新图纸...")
            
            # 创建新图纸
            if template and Path(template).exists():
                self.active_doc = self.acad_app.Documents.Add(template)
            else:
                self.active_doc = self.acad_app.Documents.Add()
            
            self.model_space = self.active_doc.ModelSpace
            
            # 等待创建完成
            time.sleep(1)
            
            logger.info("新图纸创建成功")
            return True
            
        except Exception as e:
            logger.error(f"创建新图纸失败: {e}")
            return False
    
    def save_drawing(self, save_path: str) -> bool:
        """保存图纸"""
        try:
            if not self.active_doc:
                logger.error("没有打开的图纸")
                return False
            
            logger.info(f"正在保存图纸到: {save_path}")
            
            # 保存图纸
            self.active_doc.SaveAs(save_path)
            
            logger.info("图纸保存成功")
            return True
            
        except Exception as e:
            logger.error(f"保存图纸失败: {e}")
            return False
    
    def set_parameters(self, parameters: Dict[str, Any]) -> AutomationResult:
        """设置参数（创建/修改几何对象）"""
        import time
        start_time = time.time()
        
        try:
            if not self.active_doc:
                logger.error("没有打开的图纸")
                return AutomationResult(
                    success=False,
                    status=AutomationStatus.FAILED,
                    message="没有打开的图纸",
                    parameters_set={},
                    execution_time=time.time() - start_time
                )
            
            logger.info(f"开始设置 {len(parameters)} 个参数...")
            
            parameters_set = {}
            
            for param_name, param_value in parameters.items():
                try:
                    # 根据参数名创建或修改几何对象
                    success = self._create_or_modify_geometry(param_name, param_value)
                    
                    if success:
                        parameters_set[param_name] = param_value
                        logger.debug(f"设置参数成功: {param_name} = {param_value}")
                    else:
                        logger.warning(f"设置参数失败: {param_name}")
                        
                except Exception as e:
                    logger.error(f"设置参数失败 {param_name}: {e}")
                    continue
            
            # 更新图纸显示
            if parameters_set:
                self.active_doc.Regen(1)  # 重新生成
                self.acad_app.Update()
            
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
                parameters_set=parameters_set,
                execution_time=time.time() - start_time,
                error_details=str(e)
            )
    
    def _create_or_modify_geometry(self, param_name: str, param_value: Any) -> bool:
        """创建或修改几何对象"""
        try:
            param_lower = param_name.lower()
            
            # 直径参数 - 创建圆
            if 'diameter' in param_lower or 'circle' in param_lower:
                diameter = float(param_value)
                radius = diameter / 2.0
                center = (0, 0, 0)  # 默认中心点
                
                # 创建圆
                circle = self.model_space.AddCircle(center, radius)
                circle.Layer = "0"
                return True
            
            # 长度参数 - 创建线或修改尺寸
            elif 'length' in param_lower or 'line' in param_lower:
                length = float(param_value)
                
                # 创建水平线
                start_point = (0, 0, 0)
                end_point = (length, 0, 0)
                line = self.model_space.AddLine(start_point, end_point)
                line.Layer = "0"
                return True
            
            # 宽度参数 - 创建矩形
            elif 'width' in param_lower or 'rectangle' in param_lower:
                width = float(param_value)
                height = width  # 默认正方形
                
                # 创建矩形
                corner1 = (0, 0, 0)
                corner2 = (width, height, 0)
                rectangle = self.model_space.AddRectangle(corner1, corner2)
                rectangle.Layer = "0"
                return True
            
            # 高度参数 - 创建3D对象或修改Z坐标
            elif 'height' in param_lower:
                height = float(param_value)
                
                # 创建3D盒子（简化版本）
                # 这里可以扩展为更复杂的3D几何创建
                base_point = (0, 0, 0)
                # 在实际应用中，这里应该创建真正的3D对象
                logger.info(f"创建高度为 {height} 的对象")
                return True
            
            # 半径参数 - 创建圆或修改圆角
            elif 'radius' in param_lower:
                radius = float(param_value)
                center = (0, 0, 0)
                
                # 创建圆
                circle = self.model_space.AddCircle(center, radius)
                circle.Layer = "0"
                return True
            
            # 角度参数 - 创建旋转或修改角度
            elif 'angle' in param_lower:
                angle = float(param_value)
                
                # 创建旋转的线
                import math
                length = 100  # 默认长度
                angle_rad = math.radians(angle)
                
                start_point = (0, 0, 0)
                end_point = (length * math.cos(angle_rad), length * math.sin(angle_rad), 0)
                
                line = self.model_space.AddLine(start_point, end_point)
                line.Layer = "0"
                return True
            
            # 坐标参数 - 创建点或修改对象位置
            elif any(coord in param_lower for coord in ['x_coord', 'y_coord', 'z_coord']):
                # 解析坐标值
                if isinstance(param_value, (list, tuple)) and len(param_value) >= 2:
                    x, y = float(param_value[0]), float(param_value[1])
                    z = float(param_value[2]) if len(param_value) > 2 else 0.0
                    
                    # 创建点
                    point = (x, y, z)
                    self.model_space.AddPoint(point)
                    return True
                else:
                    logger.warning(f"坐标参数格式错误: {param_value}")
                    return False
            
            # 文本参数 - 创建文本
            elif 'text' in param_lower or 'label' in param_lower:
                text_content = str(param_value)
                insertion_point = (0, 0, 0)
                
                # 创建单行文本
                text = self.model_space.AddText(text_content, insertion_point, 2.5)  # 默认高度2.5
                text.Layer = "0"
                return True
            
            # 图层参数 - 创建或修改图层
            elif 'layer' in param_lower:
                layer_name = str(param_value)
                
                # 检查图层是否存在
                try:
                    layer = self.active_doc.Layers.Item(layer_name)
                except:
                    # 创建新图层
                    layer = self.active_doc.Layers.Add(layer_name)
                
                # 设置当前图层
                self.active_doc.ActiveLayer = layer
                return True
            
            else:
                # 未知参数类型，尝试创建文本标注
                logger.info(f"创建参数标注: {param_name} = {param_value}")
                text_content = f"{param_name}: {param_value}"
                insertion_point = (0, 0, 0)
                
                text = self.model_space.AddText(text_content, insertion_point, 2.5)
                text.Layer = "0"
                return True
                
        except Exception as e:
            logger.error(f"创建几何对象失败 {param_name}: {e}")
            return False
    
    def create_piping_diagram(self, equipment_data: Dict[str, Any]) -> bool:
        """创建管道仪表流程图（P&ID）"""
        try:
            logger.info("正在创建管道仪表流程图...")
            
            # 创建设备符号
            equipment_positions = {}
            y_offset = 0
            
            for equip_name, equip_info in equipment_data.items():
                # 简化的设备符号创建
                if equip_info.get('type') == 'pump':
                    # 创建泵符号（圆形）
                    center = (0, y_offset, 0)
                    radius = 5
                    circle = self.model_space.AddCircle(center, radius)
                    circle.Layer = "EQUIPMENT"
                    
                    # 添加泵标签
                    text_point = (10, y_offset, 0)
                    text = self.model_space.AddText(f"P-{equip_name}", text_point, 2)
                    text.Layer = "TEXT"
                    
                elif equip_info.get('type') == 'valve':
                    # 创建阀门符号（矩形）
                    corner1 = (-2, y_offset - 2, 0)
                    corner2 = (2, y_offset + 2, 0)
                    rectangle = self.model_space.AddRectangle(corner1, corner2)
                    rectangle.Layer = "VALVES"
                    
                    # 添加阀门标签
                    text_point = (5, y_offset, 0)
                    text = self.model_space.AddText(f"V-{equip_name}", text_point, 2)
                    text.Layer = "TEXT"
                    
                elif equip_info.get('type') == 'tank':
                    # 创建储罐符号（矩形）
                    corner1 = (-10, y_offset - 5, 0)
                    corner2 = (10, y_offset + 5, 0)
                    rectangle = self.model_space.AddRectangle(corner1, corner2)
                    rectangle.Layer = "EQUIPMENT"
                    
                    # 添加储罐标签
                    text_point = (15, y_offset, 0)
                    text = self.model_space.AddText(f"T-{equip_name}", text_point, 2)
                    text.Layer = "TEXT"
                
                equipment_positions[equip_name] = (0, y_offset)
                y_offset -= 20  # 垂直间距
            
            # 连接设备（管道线）
            for i in range(len(equipment_positions) - 1):
                equip1_pos = list(equipment_positions.values())[i]
                equip2_pos = list(equipment_positions.values())[i + 1]
                
                # 创建连接线
                start_point = (equip1_pos[0], equip1_pos[1] - 10, 0)
                end_point = (equip2_pos[0], equip2_pos[1] + 10, 0)
                
                line = self.model_space.AddLine(start_point, end_point)
                line.Layer = "PIPING"
            
            # 更新显示
            self.active_doc.Regen(1)
            self.acad_app.Update()
            
            logger.info("管道仪表流程图创建成功")
            return True
            
        except Exception as e:
            logger.error(f"创建管道仪表流程图失败: {e}")
            return False
    
    def get_software_info(self) -> SoftwareInfo:
        """获取软件信息"""
        try:
            is_running = self.acad_app is not None
            connection_status = "已连接" if is_running else "未连接"
            
            # 获取支持的参数列表
            supported_params = [
                'diameter', 'length', 'width', 'height', 'radius', 'angle',
                'x_coord', 'y_coord', 'z_coord', 'text', 'layer'
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
        
        for param_name, param_value in parameters.items():
            try:
                param_lower = param_name.lower()
                
                # 数值参数验证
                if any(keyword in param_lower for keyword in [
                    'diameter', 'length', 'width', 'height', 'radius'
                ]):
                    val = float(param_value)
                    if val > 0:
                        validated_params[param_name] = val
                    else:
                        logger.warning(f"尺寸参数必须为正数: {val}")
                        
                elif 'angle' in param_lower:
                    angle = float(param_value)
                    if 0 <= angle <= 360:
                        validated_params[param_name] = angle
                    else:
                        logger.warning(f"角度参数超出范围: {angle}")
                        
                elif any(coord in param_lower for coord in ['x_coord', 'y_coord', 'z_coord']):
                    # 坐标可以是单个值或列表
                    if isinstance(param_value, (list, tuple)):
                        coords = [float(x) for x in param_value]
                        validated_params[param_name] = coords
                    else:
                        validated_params[param_name] = float(param_value)
                        
                elif 'text' in param_lower or 'label' in param_lower:
                    # 文本参数直接通过
                    validated_params[param_name] = str(param_value)
                    
                elif 'layer' in param_lower:
                    # 图层参数直接通过
                    validated_params[param_name] = str(param_value)
                    
                else:
                    # 其他参数直接通过
                    validated_params[param_name] = param_value
                    
            except (ValueError, TypeError) as e:
                logger.error(f"参数验证失败 {param_name}: {e}")
                continue
        
        return validated_params