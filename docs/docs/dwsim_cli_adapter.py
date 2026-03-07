"""
DWSIM命令行适配器
基于DWSIM原始CommandLineProcessor实现
"""

import asyncio
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import tempfile
import shutil

logger = logging.getLogger(__name__)

class DWSIMCLIAdapter:
    """DWSIM命令行接口适配器"""
    
    def __init__(self, dwsim_path: str = "DWSIM.exe"):
        self.dwsim_path = dwsim_path
        self.work_dir = None
        
    async def create_simulation(self, config: Dict[str, Any]) -> str:
        """创建仿真项目"""
        try:
            # 创建工作目录
            self.work_dir = Path(tempfile.mkdtemp(prefix="dwsim_"))
            
            # 创建XML配置文件
            xml_config = self._generate_xml_config(config)
            config_file = self.work_dir / "input.xml"
            config_file.write_text(xml_config)
            
            # 创建仿真项目文件
            sim_file = self.work_dir / "process.dwsim"
            
            logger.info(f"创建DWSIM项目: {sim_file}")
            return str(sim_file)
            
        except Exception as e:
            logger.error(f"创建DWSIM项目失败: {e}")
            raise
    
    async def run_simulation(self, sim_file: str, input_file: str) -> Dict[str, Any]:
        """运行仿真"""
        try:
            work_dir = Path(sim_file).parent
            output_file = work_dir / "output.xml"
            
            # 构建命令行参数
            cmd = [
                self.dwsim_path,
                "-CommandLine",
                "-nosplash",
                "-simfile", str(sim_file),
                "-input", str(input_file),
                "-output", str(output_file)
            ]
            
            logger.info(f"执行DWSIM命令: {' '.join(cmd)}")
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(work_dir)
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise RuntimeError(f"DWSIM执行失败: {error_msg}")
            
            # 解析结果
            results = self._parse_results(output_file)
            
            logger.info("DWSIM执行完成")
            return results
            
        except Exception as e:
            logger.error(f"DWSIM仿真执行失败: {e}")
            raise
    
    def _generate_xml_config(self, config: Dict[str, Any]) -> str:
        """生成XML配置文件"""
        xml = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml.append('<SimulationConfig>')
        
        # 添加化合物
        if 'compounds' in config:
            xml.append('  <Compounds>')
            for compound in config['compounds']:
                xml.append(f'    <Compound name="{compound["name"]}" />')
            xml.append('  </Compounds>')
        
        # 添加流程图
        if 'flowsheet' in config:
            xml.append('  <Flowsheet>')
            for unit in config['flowsheet'].get('units', []):
                xml.append(f'    <UnitOperation type="{unit["type"]}" name="{unit["name"]}" />')
            xml.append('  </Flowsheet>')
        
        xml.append('</SimulationConfig>')
        return '\n'.join(xml)
    
    def _parse_results(self, output_file: Path) -> Dict[str, Any]:
        """解析仿真结果"""
        try:
            if not output_file.exists():
                return {"status": "error", "message": "输出文件不存在"}
            
            # 解析XML结果
            tree = ET.parse(output_file)
            root = tree.getroot()
            
            results = {
                "status": "completed",
                "streams": [],
                "units": [],
                "convergence": True
            }
            
            # 获取物流数据
            for stream in root.findall('.//MaterialStream'):
                stream_data = {
                    "name": stream.get('name'),
                    "temperature": float(stream.find('Temperature').text),
                    "pressure": float(stream.find('Pressure').text),
                    "flowrate": float(stream.find('MolarFlow').text)
                }
                results["streams"].append(stream_data)
            
            return results
            
        except Exception as e:
            logger.error(f"解析结果失败: {e}")
            return {"status": "error", "message": str(e)}
    
    async def cleanup(self, work_dir: str):
        """清理工作目录"""
        try:
            if Path(work_dir).exists():
                shutil.rmtree(work_dir)
                logger.info(f"清理工作目录: {work_dir}")
        except Exception as e:
            logger.warning(f"清理目录失败: {e}")

# 工厂函数
async def get_dwsim_adapter() -> DWSIMCLIAdapter:
    """获取DWSIM适配器实例"""
    return DWSIMCLIAdapter()
