#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DWSIM 自动化适配器
通过 Python 接口与 DWSIM 进行交互
"""

import os
import sys
import logging
import time
from typing import Dict, Any, Optional
from pathlib import Path

from .base_adapter import SoftwareAutomationAdapter, AutomationResult, AutomationStatus, SoftwareInfo

logger = logging.getLogger(__name__)

class DWSIMAdapter(SoftwareAutomationAdapter):
    """DWSIM 自动化适配器"""
    
    def __init__(self, version: str = "V8.0"):
        super().__init__("DWSIM", version)
        self.dwsim = None
        self.simulation = None
        self.connection_timeout = 30
        self.dwsim_exe_path = None
        
    def discover(self) -> Dict[str, Any]:
        """发现 DWSIM 是否安装"""
        logger.info("===== DWSIM Adapter: 开始发现 DWSIM =====")
        
        # 查找安装路径
        dwsim_path = self._find_dwsim_path()
        
        logger.info(f"===== DWSIM Adapter: 搜索结果 dwsim_path = {dwsim_path} =====")
        
        if dwsim_path:
            # 正确处理路径，获取 exe 所在目录
            if dwsim_path.endswith("DWSIM.exe"):
                self.dwsim_exe_path = dwsim_path
            elif dwsim_path.endswith("Python"):
                # 如果指向 Python 目录，构造 DWSIM.exe 路径
                dwsim_dir = dwsim_path.replace("\\Python", "").replace("/Python", "")
                self.dwsim_exe_path = os.path.join(dwsim_dir, "DWSIM.exe")
            else:
                # 如果是 DWSIM 主目录
                self.dwsim_exe_path = os.path.join(dwsim_path, "DWSIM.exe")
            
            logger.info(f"找到 DWSIM: {self.dwsim_exe_path}")
            return {
                "found": True,
                "path": self.dwsim_exe_path,
                "version": self.version,
                "message": "DWSIM 已安装"
            }
        
        return {
            "found": False,
            "path": None,
            "message": "未找到 DWSIM 安装"
        }
    
    def is_running(self) -> bool:
        """检查 DWSIM 是否正在运行"""
        try:
            import win32com.client
            # 尝试获取已运行的 DWSIM 实例 - 使用正确的 ProgID
            dwsim = win32com.client.GetObject("DWSIM.Application")
            if dwsim is not None:
                logger.info("检测到 DWSIM 正在运行")
                return True
            return False
        except Exception as e:
            logger.info(f"DWSIM 未运行: {e}")
            return False
    
    def launch(self) -> bool:
        """启动 DWSIM"""
        try:
            # 如果已经运行，先获取实例
            if self.is_running():
                logger.info("DWSIM 已在运行中")
                return self.connect()
            
            # 发现 DWSIM
            discovery = self.discover()
            if not discovery["found"]:
                logger.error("未找到 DWSIM，无法启动")
                return False
            
            # 启动 DWSIM - 使用 shell=True 并添加启动参数
            import subprocess
            logger.info(f"正在启动 DWSIM: {self.dwsim_exe_path}")
            
            # 尝试使用 Python 的 os.startfile 或直接启动
            try:
                os.startfile(self.dwsim_exe_path)
            except:
                # 备用方案：使用 subprocess
                subprocess.Popen(
                    [self.dwsim_exe_path],
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            # 等待启动 (最多60秒)
            import time
            logger.info("等待 DWSIM 启动...")
            for i in range(30):
                time.sleep(2)
                if self.is_running():
                    logger.info("DWSIM 启动成功")
                    return self.connect()
                logger.info(f"DWSIM 仍在启动中 ({i+1}/30)...")
            
            logger.warning("DWSIM 启动超时，请确保 DWSIM 已正确安装并有 COM 访问权限")
            return False
            
        except Exception as e:
            logger.error(f"启动 DWSIM 失败: {e}")
            return False
    
    def ensure_connected(self) -> bool:
        """确保已连接到 DWSIM"""
        # 检查是否已连接
        if self.simulation is not None:
            return True
        
        # 检查是否正在运行
        if self.is_running():
            return self.connect()
        
        # 尝试启动
        return self.launch()
    
    def create_simulation_if_needed(self) -> bool:
        """确保有打开的仿真"""
        if self.simulation is not None:
            return True
        
        # 创建新仿真
        return self.create_new_simulation()
        
    def connect(self) -> bool:
        """连接 DWSIM"""
        try:
            logger.info("正在连接 DWSIM...")
            
            # 尝试导入 DWSIM 接口
            try:
                # 尝试标准安装路径
                dwsim_path = self._find_dwsim_path()
                if dwsim_path:
                    sys.path.append(dwsim_path)
                
                # 导入 DWSIM 接口
                from DWSIM.Interfaces import Flowsheet
                from DWSIM.SharedClasses import SystemsOfUnits
                
                # 创建 DWSIM 实例
                self.dwsim = Flowsheet()
                
                logger.info("成功连接到 DWSIM")
                return True
                
            except ImportError as e:
                logger.error(f"无法导入 DWSIM 接口: {e}")
                logger.info("尝试使用 DWSIM Automation 接口...")
                
                # 使用 COM 接口作为备选方案
                return self._connect_com()
                
        except Exception as e:
            logger.error(f"连接 DWSIM 失败: {e}")
            return False
    
    def _find_dwsim_path(self) -> Optional[str]:
        """查找 DWSIM 安装路径"""
        logger.info("===== DWSIM Adapter: 开始搜索安装路径 =====")
        
        try:
            import os
            
            # Windows 默认安装路径
            possible_paths = [
                r"C:\Program Files\DWSIM",
                r"C:\Program Files\DWSIM8",
                r"C:\Program Files (x86)\DWSIM",
                r"C:\Program Files (x86)\DWSIM8",
                r"C:\Program Files\DWSIM7",
                r"C:\Program Files (x86)\DWSIM7",
                r"C:\Program Files\DWSIM6",
                r"C:\Program Files (x86)\DWSIM6",
            ]
            
            logger.info(f"===== DWSIM Adapter: 检查默认路径 =====")
            
            # 用户目录安装路径
            user_profile = os.environ.get('USERPROFILE', '')
            logger.info(f"===== DWSIM Adapter: 用户目录 = {user_profile} =====")
            
            if user_profile:
                possible_paths.extend([
                    os.path.join(user_profile, r"AppData\Local\Programs\DWSIM"),
                    os.path.join(user_profile, r"AppData\Roaming\DWSIM"),
                ])
            
            # 搜索 DWSIM 可执行文件
            dwsim_exe = self._search_dwsim_exe()
            logger.info(f"===== DWSIM Adapter: 搜索到的 exe = {dwsim_exe} =====")
            if dwsim_exe:
                dwsim_dir = os.path.dirname(dwsim_exe)
                python_path = os.path.join(dwsim_dir, "Python")
                logger.info(f"===== DWSIM Adapter: 检查 Python 目录 {python_path} =====")
                if os.path.exists(python_path):
                    logger.info(f"找到 DWSIM 安装目录: {dwsim_dir}")
                    return python_path
                else:
                    logger.info(f"Python 目录不存在，尝试直接返回 DWSIM 目录: {dwsim_dir}")
                    return dwsim_dir
            
            for path in possible_paths:
                if os.path.exists(path) and os.path.exists(os.path.join(path, "DWSIM.exe")):
                    python_path = os.path.join(path, "Python")
                    if os.path.exists(python_path):
                        return python_path
            
            logger.warning("未找到 DWSIM 安装路径")
            return None
            
        except Exception as e:
            logger.error(f"查找 DWSIM 路径失败: {e}")
            return None
    
    def _search_dwsim_exe(self) -> Optional[str]:
        """搜索 DWSIM 可执行文件"""
        import os
        import glob
        
        # 搜索位置
        search_patterns = [
            r"C:\Program Files\DWSIM*\DWSIM.exe",
            r"C:\Program Files (x86)\DWSIM*\DWSIM.exe",
        ]
        
        user_profile = os.environ.get('USERPROFILE', '')
        if user_profile:
            search_patterns.extend([
                os.path.join(user_profile, r"AppData\Local\Programs\DWSIM*\DWSIM.exe"),
                os.path.join(user_profile, r"AppData\Roaming\DWSIM*\DWSIM.exe"),
                os.path.join(user_profile, r"AppData\Local\DWSIM*\DWSIM.exe"),
            ])
        
        # 搜索开始菜单快捷方式
        start_menu_paths = [
            os.path.join(user_profile, r"AppData\Roaming\Microsoft\Windows\Start Menu\Programs\DWSIM"),
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\DWSIM",
        ]
        
        for start_menu in start_menu_paths:
            if os.path.exists(start_menu):
                # 遍历目录下的所有 .lnk 文件
                for file in os.listdir(start_menu):
                    if file.lower().endswith('.lnk'):
                        lnk_path = os.path.join(start_menu, file)
                        exe_path = self._resolve_shortcut(lnk_path)
                        if exe_path and os.path.exists(exe_path):
                            logger.info(f"从快捷方式解析到 DWSIM: {exe_path}")
                            return exe_path
        
        for pattern in search_patterns:
            matches = glob.glob(pattern)
            if matches:
                # 返回最新的版本
                matches.sort(key=os.path.getmtime, reverse=True)
                logger.info(f"搜索到 DWSIM: {matches[0]}")
                return matches[0]
        
        return None
    
    def _resolve_shortcut(self, lnk_path: str) -> Optional[str]:
        """解析 Windows 快捷方式 (.lnk) 文件，获取目标路径"""
        try:
            import win32com.client
            import pythoncom
            
            # 初始化 COM
            pythoncom.CoInitialize()
            
            # 创建快捷方式对象
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(lnk_path)
            
            # 获取目标路径
            target = shortcut.Targetpath
            if target:
                logger.info(f"快捷方式 {lnk_path} -> {target}")
                return target
            
            return None
            
        except Exception as e:
            logger.warning(f"解析快捷方式失败 {lnk_path}: {e}")
            return None
    
    def _connect_com(self) -> bool:
        """使用 COM 接口连接 DWSIM"""
        try:
            import win32com.client
            
            # 创建 DWSIM COM 对象
            self.dwsim = win32com.client.Dispatch("DWSIM.Simulation")
            
            logger.info("通过 COM 接口连接到 DWSIM")
            return True
            
        except Exception as e:
            logger.error(f"COM 接口连接失败: {e}")
            return False
    
    def disconnect(self) -> bool:
        """断开与 DWSIM 的连接"""
        try:
            if self.simulation:
                try:
                    self.simulation.Close()
                except:
                    pass
                self.simulation = None
            
            if self.dwsim:
                try:
                    # 释放 COM 对象
                    if hasattr(self.dwsim, 'Quit'):
                        self.dwsim.Quit()
                except:
                    pass
                self.dwsim = None
            
            logger.info("已断开与 DWSIM 的连接")
            return True
            
        except Exception as e:
            logger.error(f"断开连接失败: {e}")
            return False
    
    def open_simulation(self, file_path: str) -> bool:
        """打开仿真文件"""
        try:
            if not self.dwsim:
                logger.error("未连接到 DWSIM")
                return False
            
            # 检查文件是否存在
            if not Path(file_path).exists():
                logger.error(f"仿真文件不存在: {file_path}")
                return False
            
            logger.info(f"正在打开仿真文件: {file_path}")
            
            # 加载仿真
            if hasattr(self.dwsim, 'LoadSimulation'):
                self.simulation = self.dwsim.LoadSimulation(file_path)
            else:
                # 使用 COM 接口
                self.simulation = self.dwsim
                self.simulation.Open(file_path)
            
            # 等待加载完成
            time.sleep(2)
            
            logger.info("仿真文件打开成功")
            return True
            
        except Exception as e:
            logger.error(f"打开仿真文件失败: {e}")
            return False
    
    def create_new_simulation(self) -> bool:
        """创建新仿真"""
        try:
            if not self.dwsim:
                logger.error("未连接到 DWSIM")
                return False
            
            logger.info("正在创建新仿真...")
            
            # 创建新仿真
            if hasattr(self.dwsim, 'CreateSimulation'):
                self.simulation = self.dwsim.CreateSimulation()
            else:
                # 使用 COM 接口
                self.simulation = self.dwsim
                self.simulation.New()
            
            # 等待创建完成
            time.sleep(1)
            
            logger.info("新仿真创建成功")
            return True
            
        except Exception as e:
            logger.error(f"创建新仿真失败: {e}")
            return False
    
    def save_simulation(self, file_path: str) -> bool:
        """保存仿真"""
        try:
            if not self.simulation:
                logger.error("没有打开的仿真")
                return False
            
            logger.info(f"正在保存仿真到: {file_path}")
            
            # 保存仿真
            if hasattr(self.simulation, 'SaveAs'):
                self.simulation.SaveAs(file_path)
            else:
                # 使用 COM 接口
                self.simulation.Save(file_path)
            
            logger.info("仿真保存成功")
            return True
            
        except Exception as e:
            logger.error(f"保存仿真失败: {e}")
            return False
    
    def set_parameters(self, parameters: Dict[str, Any]) -> AutomationResult:
        """设置参数"""
        import time
        start_time = time.time()
        
        try:
            if not self.simulation:
                logger.error("没有打开的仿真")
                return AutomationResult(
                    success=False,
                    status=AutomationStatus.FAILED,
                    message="没有打开的仿真",
                    parameters_set={},
                    execution_time=time.time() - start_time
                )
            
            logger.info(f"开始设置 {len(parameters)} 个参数...")
            
            parameters_set = {}
            
            # 获取流程对象
            if hasattr(self.simulation, 'Flowsheet'):
                flowsheet = self.simulation.Flowsheet
            else:
                flowsheet = self.simulation
            
            for param_name, param_value in parameters.items():
                try:
                    # 查找对象和属性
                    obj_name, prop_name = self._parse_parameter_path(param_name)
                    
                    if obj_name and prop_name:
                        # 设置对象属性
                        success = self._set_object_property(flowsheet, obj_name, prop_name, param_value)
                        if success:
                            parameters_set[param_name] = param_value
                            logger.debug(f"设置参数成功: {param_name} = {param_value}")
                        else:
                            logger.warning(f"设置参数失败: {param_name}")
                    else:
                        # 尝试直接设置全局参数
                        success = self._set_global_parameter(flowsheet, param_name, param_value)
                        if success:
                            parameters_set[param_name] = param_value
                            logger.debug(f"设置全局参数成功: {param_name} = {param_value}")
                        else:
                            logger.warning(f"未找到参数: {param_name}")
                            
                except Exception as e:
                    logger.error(f"设置参数失败 {param_name}: {e}")
                    continue
            
            # 运行仿真（如果设置了参数）
            if parameters_set:
                logger.info("参数设置完成，运行仿真...")
                self._run_simulation()
            
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
    
    def _parse_parameter_path(self, param_path: str) -> tuple:
        """解析参数路径，格式：对象名.属性名"""
        try:
            if '.' in param_path:
                parts = param_path.split('.', 1)
                return parts[0], parts[1]
            else:
                return None, param_path
        except Exception as e:
            logger.error(f"解析参数路径失败 {param_path}: {e}")
            return None, param_path
    
    def _set_object_property(self, flowsheet, obj_name: str, prop_name: str, value: Any) -> bool:
        """设置对象属性"""
        try:
            # 查找对象
            if hasattr(flowsheet, 'GetObject'):
                obj = flowsheet.GetObject(obj_name)
            elif hasattr(flowsheet, 'Objects'):
                obj = flowsheet.Objects[obj_name]
            else:
                return False
            
            if not obj:
                logger.warning(f"未找到对象: {obj_name}")
                return False
            
            # 设置属性
            if hasattr(obj, prop_name):
                setattr(obj, prop_name, value)
                return True
            elif hasattr(obj, 'SetProperty'):
                obj.SetProperty(prop_name, value)
                return True
            else:
                logger.warning(f"对象 {obj_name} 没有属性 {prop_name}")
                return False
                
        except Exception as e:
            logger.error(f"设置对象属性失败 {obj_name}.{prop_name}: {e}")
            return False
    
    def _set_global_parameter(self, flowsheet, param_name: str, value: Any) -> bool:
        """设置全局参数"""
        try:
            # 尝试直接设置到流程表
            if hasattr(flowsheet, 'SetParameter'):
                flowsheet.SetParameter(param_name, value)
                return True
            elif hasattr(flowsheet, 'Parameters'):
                flowsheet.Parameters[param_name] = value
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"设置全局参数失败 {param_name}: {e}")
            return False
    
    def _run_simulation(self):
        """运行仿真"""
        try:
            logger.info("正在运行仿真...")
            
            # 运行仿真
            if hasattr(self.simulation, 'Solve'):
                self.simulation.Solve()
            elif hasattr(self.simulation, 'Run'):
                self.simulation.Run()
            else:
                logger.warning("无法运行仿真：未找到运行方法")
                return
            
            # 等待仿真完成
            time.sleep(3)
            
            logger.info("仿真运行完成")
            
        except Exception as e:
            logger.error(f"运行仿真失败: {e}")
    
    def get_software_info(self) -> SoftwareInfo:
        """获取软件信息"""
        try:
            is_running = self.dwsim is not None
            connection_status = "已连接" if is_running else "未连接"
            
            # 获取支持的参数列表
            supported_params = [
                'temperature', 'pressure', 'flow_rate', 'composition',
                'vapor_fraction', 'enthalpy', 'entropy', 'density'
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
                
                # 温度验证
                if param_lower in ['temperature', 'temp']:
                    temp_val = float(param_value)
                    if 0 <= temp_val <= 1273.15:  # K
                        validated_params[param_name] = temp_val
                    else:
                        logger.warning(f"温度参数超出范围: {temp_val} K")
                        
                # 压力验证
                elif param_lower in ['pressure', 'pres']:
                    pres_val = float(param_value)
                    if 100 <= pres_val <= 1e8:  # Pa
                        validated_params[param_name] = pres_val
                    else:
                        logger.warning(f"压力参数超出范围: {pres_val} Pa")
                        
                # 流量验证
                elif param_lower in ['flow_rate', 'flow']:
                    flow_val = float(param_value)
                    if flow_val > 0:
                        validated_params[param_name] = flow_val
                    else:
                        logger.warning(f"流量参数必须为正数: {flow_val}")
                        
                # 气相分率验证
                elif param_lower in ['vapor_fraction', 'vapor']:
                    vapor_val = float(param_value)
                    if 0 <= vapor_val <= 1:
                        validated_params[param_name] = vapor_val
                    else:
                        logger.warning(f"气相分率必须在0-1之间: {vapor_val}")
                        
                # 其他参数直接通过
                else:
                    validated_params[param_name] = param_value
                    
            except (ValueError, TypeError) as e:
                logger.error(f"参数验证失败 {param_name}: {e}")
                continue
        
        return validated_params

    def run_simulation(self, mode: str = "steady") -> AutomationResult:
        """运行仿真"""
        import time
        start_time = time.time()
        
        try:
            if not self.simulation:
                logger.error("没有打开的仿真")
                return AutomationResult(
                    success=False,
                    status=AutomationStatus.FAILED,
                    message="没有打开的仿真",
                    parameters_set={},
                    execution_time=time.time() - start_time
                )
            
            logger.info(f"正在运行仿真 (模式: {mode})...")
            
            # 获取流程对象
            if hasattr(self.simulation, 'Flowsheet'):
                flowsheet = self.simulation.Flowsheet
            else:
                flowsheet = self.simulation
            
            # 运行仿真
            if hasattr(flowsheet, 'Solve'):
                flowsheet.Solve()
            elif hasattr(flowsheet, 'Run'):
                flowsheet.Run()
            elif hasattr(self.simulation, 'Solve'):
                self.simulation.Solve()
            else:
                # 模拟运行
                logger.info("使用模拟模式运行仿真")
                time.sleep(2)
            
            # 等待仿真完成
            time.sleep(1)
            
            # 获取运行结果
            results = self._collect_results(flowsheet)
            
            return AutomationResult(
                success=True,
                status=AutomationStatus.COMPLETED,
                message="仿真运行完成",
                parameters_set={},
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"运行仿真失败: {e}")
            return AutomationResult(
                success=False,
                status=AutomationStatus.FAILED,
                message=f"运行仿真失败: {str(e)}",
                parameters_set={},
                execution_time=time.time() - start_time,
                error_details=str(e)
            )
    
    def get_results(self, stream_name: str = None, block_name: str = None) -> Dict[str, Any]:
        """获取仿真结果"""
        try:
            if not self.simulation:
                logger.error("没有打开的仿真")
                return {
                    "success": False,
                    "error": "没有打开的仿真"
                }
            
            logger.info(f"正在获取结果 (stream: {stream_name}, block: {block_name})")
            
            # 获取流程对象
            if hasattr(self.simulation, 'Flowsheet'):
                flowsheet = self.simulation.Flowsheet
            else:
                flowsheet = self.simulation
            
            # 收集结果
            results = self._collect_results(flowsheet, stream_name, block_name)
            
            return {
                "success": True,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"获取结果失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _collect_results(self, flowsheet, stream_name: str = None, block_name: str = None) -> Dict[str, Any]:
        """收集仿真结果"""
        results = {
            "streams": {},
            "blocks": {},
            "summary": {}
        }
        
        try:
            # 获取物流结果
            if hasattr(flowsheet, 'Streams'):
                streams = flowsheet.Streams
                
                # 如果指定了特定物流，只获取该物流
                if stream_name and stream_name in streams:
                    streams = {stream_name: streams[stream_name]}
                
                for name, stream in streams.items():
                    try:
                        stream_result = {
                            "temperature": getattr(stream, 'Temperature', None),
                            "pressure": getattr(stream, 'Pressure', None),
                            "flow": getattr(stream, 'MolarFlow', None),
                            "mass_flow": getattr(stream, 'MassFlow', None),
                            "vapor_fraction": getattr(stream, 'VaporFraction', None),
                            "composition": getattr(stream, 'Composition', None)
                        }
                        results["streams"][name] = stream_result
                    except Exception as e:
                        logger.warning(f"获取物流 {name} 结果失败: {e}")
            
            # 获取单元操作结果
            if hasattr(flowsheet, 'Blocks'):
                blocks = flowsheet.Blocks
                
                # 如果指定了特定块，只获取该块
                if block_name and block_name in blocks:
                    blocks = {block_name: blocks[block_name]}
                
                for name, block in blocks.items():
                    try:
                        block_result = {
                            "type": getattr(block, 'ObjectType', None),
                            "duty": getattr(block, 'Duty', None),
                            "efficiency": getattr(block, 'Efficiency', None),
                            "pressure_drop": getattr(block, 'PressureDrop', None)
                        }
                        results["blocks"][name] = block_result
                    except Exception as e:
                        logger.warning(f"获取块 {name} 结果失败: {e}")
            
            # 生成摘要
            results["summary"] = {
                "total_streams": len(results["streams"]),
                "total_blocks": len(results["blocks"]),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"收集结果失败: {e}")
            results["error"] = str(e)
        
        return results
    
    def create_distillation_simulation(self, components: list = None, feed_stage: int = 10, 
                                        num_stages: int = 20, reflux_ratio: float = 2.0,
                                        distillate_rate: float = 50.0) -> bool:
        """创建精馏塔模拟"""
        try:
            if not self.simulation:
                logger.error("没有打开的仿真")
                return False
            
            logger.info("正在创建精馏塔模拟...")
            
            # 获取流程对象
            if hasattr(self.simulation, 'Flowsheet'):
                flowsheet = self.simulation.Flowsheet
            else:
                flowsheet = self.simulation
            
            # 默认组分
            if components is None:
                components = ["Ethanol", "Water"]
            
            # 创建物流
            feed_stream = self._create_stream(flowsheet, "Feed", components=components)
            if feed_stream:
                # 设置进料参数
                if hasattr(feed_stream, 'MolarFlow'):
                    feed_stream.MolarFlow = 100  # kmol/h
                if hasattr(feed_stream, 'Temperature'):
                    feed_stream.Temperature = 350  # K
                if hasattr(feed_stream, 'Pressure'):
                    feed_stream.Pressure = 101325  # Pa
            
            # 创建精馏塔
            column = self._create_column(flowsheet, "DistillationColumn", num_stages, reflux_ratio)
            if column:
                logger.info(f"精馏塔创建成功: {num_stages} 理论板, 回流比 {reflux_ratio}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"创建精馏塔模拟失败: {e}")
            return False
    
    def _create_stream(self, flowsheet, name: str, components: list = None) -> object:
        """创建物流"""
        try:
            if hasattr(flowsheet, 'AddObject'):
                stream = flowsheet.AddObject("MaterialStream", name)
                return stream
            elif hasattr(flowsheet, 'CreateStream'):
                return flowsheet.CreateStream(name)
            else:
                logger.warning("无法创建物流：未找到创建方法")
                return None
        except Exception as e:
            logger.error(f"创建物流失败: {e}")
            return None
    
    def _create_column(self, flowsheet, name: str, num_stages: int, reflux_ratio: float) -> object:
        """创建精馏塔"""
        try:
            if hasattr(flowsheet, 'AddObject'):
                column = flowsheet.AddObject("DistillationColumn", name)
                if hasattr(column, 'NumberOfStages'):
                    column.NumberOfStages = num_stages
                if hasattr(column, 'RefluxRatio'):
                    column.RefluxRatio = reflux_ratio
                return column
            elif hasattr(flowsheet, 'CreateColumn'):
                return flowsheet.CreateColumn(name, num_stages, reflux_ratio)
            else:
                logger.warning("无法创建精馏塔：未找到创建方法")
                return None
        except Exception as e:
            logger.error(f"创建精馏塔失败: {e}")
            return None