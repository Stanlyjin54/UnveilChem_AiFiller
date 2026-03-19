#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件自动发现服务
扫描本地安装的化工/工程软件并检测其状态
"""

import os
import subprocess
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import winreg
from pathlib import Path

logger = logging.getLogger(__name__)


class SoftwareStatus(Enum):
    """软件状态"""
    INSTALLED = "installed"
    NOT_INSTALLED = "not_installed"
    RUNNING = "running"
    UNKNOWN = "unknown"


@dataclass
class DetectedSoftware:
    """检测到的软件"""
    name: str
    display_name: str
    version: str
    install_path: str
    executable_path: str
    status: SoftwareStatus
    software_type: str
    metadata: Dict[str, Any]


class SoftwareDiscovery:
    """软件自动发现服务"""

    # 已知软件的安装路径配置
    SOFTWARE_PATTERNS = {
        "dwsim": {
            "display_name": "DWSIM",
            "description": "DWSIM 化工流程模拟软件",
            "software_type": "simulation",
            "paths": [
                r"C:\Program Files\DWSIM\DWSIM.exe",
                r"C:\Program Files (x86)\DWSIM\DWSIM.exe",
                r"C:\Program Files (x86)\DWSIM 6.0\DWSIM.exe",
            ],
            "registry_keys": [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\DWSIM"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\DWSIM"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\DWSIM"),
            ]
        },
        "aspen_plus": {
            "display_name": "Aspen Plus",
            "description": "Aspen Plus 化工流程模拟软件",
            "software_type": "simulation",
            "paths": [
                r"C:\Program Files\AspenTech\Aspen Plus V14.2\xxe.exe",
                r"C:\Program Files\AspenTech\Aspen Plus V12.1\xxe.exe",
                r"C:\Program Files\AspenTech\Aspen Plus V11\xxe.exe",
            ],
            "registry_keys": [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\AspenTech"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\AspenTech"),
            ]
        },
        "excel": {
            "display_name": "Microsoft Excel",
            "description": "Microsoft Excel 电子表格",
            "software_type": "office",
            "paths": [
                r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
                r"C:\Program Files\Microsoft Office\root\Office15\EXCEL.EXE",
                r"C:\Program Files (x86)\Microsoft Office\Office16\EXCEL.EXE",
                r"C:\Program Files (x86)\Microsoft Office\Office15\EXCEL.EXE",
            ],
            "registry_keys": [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Office\ClickToRun\Configuration"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Office\16.0\Common\InstallRoot"),
            ]
        },
        "autocad": {
            "display_name": "AutoCAD",
            "description": "AutoCAD 绘图软件",
            "software_type": "cad",
            "paths": [
                r"C:\Program Files\Autodesk\AutoCAD 2024\acad.exe",
                r"C:\Program Files\Autodesk\AutoCAD 2023\acad.exe",
                r"C:\Program Files\Autodesk\AutoCAD 2022\acad.exe",
                r"C:\Program Files\Autodesk\AutoCAD 2021\acad.exe",
            ],
            "registry_keys": [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Autodesk\AutoCAD"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Autodesk\AutoCAD"),
            ]
        },
        "pro_ii": {
            "display_name": "PRO/II",
            "description": "PRO/II 化工流程模拟软件",
            "software_type": "simulation",
            "paths": [
                r"C:\Program Files\SimSci\PRO_II\PROII.exe",
                r"C:\Program Files (x86)\SimSci\PRO_II\PROII.exe",
            ],
            "registry_keys": [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\SimSci"),
            ]
        },
        "chemcad": {
            "display_name": "ChemCAD",
            "description": "ChemCAD 化工流程模拟软件",
            "software_type": "simulation",
            "paths": [
                r"C:\Program Files\ChemCAD\CC5.exe",
                r"C:\Program Files (x86)\ChemCAD\CC5.exe",
            ],
            "registry_keys": [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\ChemCAD"),
            ]
        },
        "hysys": {
            "display_name": "Aspen HYSYS",
            "description": "Aspen HYSYS 过程模拟软件",
            "software_type": "simulation",
            "paths": [
                r"C:\Program Files\AspenTech\Aspen HYSYS V14.0\HYSYS.exe",
                r"C:\Program Files\AspenTech\Aspen HYSYS V12.3\HYSYS.exe",
            ],
            "registry_keys": [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\AspenTech\HYSYS"),
            ]
        },
        "solidworks": {
            "display_name": "SolidWorks",
            "description": "SolidWorks 3D CAD 软件",
            "software_type": "cad",
            "paths": [
                r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe",
            ],
            "registry_keys": [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\SolidWorks"),
            ]
        }
    }

    def __init__(self):
        self.detected_software: List[DetectedSoftware] = []

    def scan_all(self) -> List[DetectedSoftware]:
        """扫描所有已配置的软件"""
        self.detected_software = []

        for software_id, config in self.SOFTWARE_PATTERNS.items():
            software = self._scan_software(software_id, config)
            if software:
                self.detected_software.append(software)

        logger.info(f"软件扫描完成，共发现 {len(self.detected_software)} 个软件")
        return self.detected_software

    def _scan_software(self, software_id: str, config: Dict) -> Optional[DetectedSoftware]:
        """扫描单个软件"""
        # 1. 先尝试路径扫描
        install_path = self._scan_by_paths(config.get("paths", []))

        # 2. 如果路径扫描失败，尝试注册表扫描
        if not install_path:
            install_path = self._scan_by_registry(config.get("registry_keys", []))

        if install_path:
            executable_path = self._find_executable(install_path, software_id)
            if executable_path:
                version = self._get_software_version(executable_path)
                status = self._check_running_status(executable_path)

                return DetectedSoftware(
                    name=software_id,
                    display_name=config["display_name"],
                    version=version,
                    install_path=install_path,
                    executable_path=executable_path,
                    status=status,
                    software_type=config["software_type"],
                    metadata={
                        "description": config.get("description", ""),
                        "scan_method": "path" if config.get("paths") else "registry"
                    }
                )

        return None

    def _scan_by_paths(self, paths: List[str]) -> Optional[str]:
        """通过路径扫描软件"""
        for path in paths:
            path = path.replace("*", "")
            if os.path.exists(path):
                return str(Path(path).parent)
            # 也检查带版本号的目录
            parent = Path(path).parent
            if parent.exists():
                for item in parent.iterdir():
                    if item.is_file() and item.suffix == ".exe":
                        return str(item.parent)
        return None

    def _scan_by_registry(self, registry_keys: List[tuple]) -> Optional[str]:
        """通过注册表扫描软件"""
        for hkey, key_path in registry_keys:
            try:
                with winreg.OpenKey(hkey, key_path) as key:
                    # 尝试读取安装路径
                    try:
                        install_path, _ = winreg.QueryValueEx(key, "InstallPath")
                        if install_path and os.path.exists(install_path):
                            return install_path
                    except FileNotFoundError:
                        pass

                    # 尝试读取其他可能的路径键
                    for value_name in ["Directory", "Folder", "Path"]:
                        try:
                            path, _ = winreg.QueryValueEx(key, value_name)
                            if path and os.path.exists(path):
                                return path
                        except FileNotFoundError:
                            continue
            except FileNotFoundError:
                continue
            except Exception as e:
                logger.debug(f"注册表扫描失败: {key_path} - {e}")
                continue
        return None

    def _find_executable(self, install_path: str, software_id: str) -> Optional[str]:
        """在安装目录中查找可执行文件"""
        install_path = Path(install_path)

        if not install_path.exists():
            return None

        # 常见可执行文件名模式
        exe_patterns = {
            "dwsim": ["DWSIM.exe", "dwsim.exe"],
            "aspen_plus": ["xxe.exe", "ape.exe", "AspenPlus.exe"],
            "excel": ["EXCEL.exe", "Excel.exe"],
            "autocad": ["acad.exe", "acad.exe"],
            "pro_ii": ["PROII.exe", "ProII.exe"],
            "chemcad": ["CC5.exe", "CC6.exe", "ChemCAD.exe"],
            "hysys": ["HYSYS.exe"],
            "solidworks": ["SLDWORKS.exe"]
        }

        patterns = exe_patterns.get(software_id, [f"{software_id}.exe"])

        # 在安装目录中搜索
        for pattern in patterns:
            # 直接搜索
            exe_path = install_path / pattern
            if exe_path.exists():
                return str(exe_path)

            # 递归搜索
            for item in install_path.rglob(pattern):
                if item.is_file():
                    return str(item)

        # 如果没找到，返回安装目录本身
        return str(install_path / f"{software_id}.exe") if (install_path / f"{software_id}.exe").exists() else None

    def _get_software_version(self, exe_path: str) -> str:
        """获取软件版本"""
        try:
            import win32api
            try:
                info = win32api.GetFileVersionInfo(exe_path, '\\')
                version = f"{info['FileVersionMS'] >> 16}.{info['FileVersionMS'] & 0xFFFF}.{info['FileVersionLS'] >> 16}"
                return version
            except:
                pass
        except ImportError:
            pass

        # 备选方法：使用 PowerShell 获取版本
        try:
            result = subprocess.run(
                ['powershell', '-Command', f"(Get-Item '{exe_path}').VersionInfo.FileVersion"],
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except:
            pass

        return "Unknown"

    def _check_running_status(self, executable_path: str) -> SoftwareStatus:
        """检查软件运行状态"""
        try:
            exe_name = Path(executable_path).name
            # 使用 tasklist 检查进程
            result = subprocess.run(
                ['tasklist', '/FI', f'IMAGENAME eq {exe_name}'],
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                timeout=5
            )
            if exe_name.lower() in result.stdout.lower():
                return SoftwareStatus.RUNNING
        except:
            pass

        return SoftwareStatus.INSTALLED

    def get_software_by_type(self, software_type: str) -> List[DetectedSoftware]:
        """按类型获取软件列表"""
        return [s for s in self.detected_software if s.software_type == software_type]

    def get_simulation_software(self) -> List[DetectedSoftware]:
        """获取所有流程模拟软件"""
        return self.get_software_by_type("simulation")

    def get_cad_software(self) -> List[DetectedSoftware]:
        """获取所有 CAD 软件"""
        return self.get_software_by_type("cad")

    def get_office_software(self) -> List[DetectedSoftware]:
        """获取所有办公软件"""
        return self.get_software_by_type("office")

    def to_dict(self) -> List[Dict[str, Any]]:
        """转换为字典列表"""
        return [
            {
                "name": s.name,
                "display_name": s.display_name,
                "version": s.version,
                "install_path": s.install_path,
                "executable_path": s.executable_path,
                "status": s.status.value,
                "software_type": s.software_type,
                "description": s.metadata.get("description", ""),
            }
            for s in self.detected_software
        ]


# 全局实例
_software_discovery_instance: Optional[SoftwareDiscovery] = None


def get_software_discovery() -> SoftwareDiscovery:
    """获取软件发现服务实例"""
    global _software_discovery_instance
    if _software_discovery_instance is None:
        _software_discovery_instance = SoftwareDiscovery()
    return _software_discovery_instance


def scan_local_software() -> List[Dict[str, Any]]:
    """扫描本地软件的便捷函数"""
    discovery = get_software_discovery()
    discovery.scan_all()
    return discovery.to_dict()
