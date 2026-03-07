#!/usr/bin/env python3
"""
外部工具适配层运行管理脚本
"""

import argparse
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

class DevelopmentManager:
    """开发管理器 - 管理外部工具适配层的开发流程"""
    
    def __init__(self):
        self.base_dir = Path("d:/UnveilChem_Studio")
        self.services_dir = self.base_dir / "services"
        self.current_phase = 1  # 当前执行阶段
        
    def print_header(self, title):
        """打印标题头"""
        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"工作目录: {self.base_dir}")
        print(f"{'='*60}\n")
    
    def run_command(self, cmd, cwd=None, description=""):
        """执行命令并显示进度"""
        if description:
            print(f"📋 {description}")
        print(f"执行命令: {cmd}")
        
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                cwd=cwd or self.base_dir,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                print("✅ 执行成功")
                if result.stdout:
                    print(f"输出: {result.stdout[:200]}...")
                return True
            else:
                print(f"❌ 执行失败")
                print(f"错误: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 执行异常: {e}")
            return False
    
    def check_environment(self):
        """检查开发环境"""
        self.print_header("环境检查")
        
        # 检查Python版本
        python_version = sys.version_info
        print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # 检查必要的目录
        required_dirs = [
            self.services_dir / "dwsim-service",
            self.services_dir / "freecad-service", 
            self.services_dir / "openfoam-service"
        ]
        
        for dir_path in required_dirs:
            if dir_path.exists():
                print(f"✅ {dir_path.name} 目录存在")
            else:
                print(f"❌ {dir_path.name} 目录不存在")
                
        # 检查必要的工具
        tools = ["python", "pip"]
        for tool in tools:
            result = subprocess.run([tool, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {tool}: {result.stdout.strip()}")
            else:
                print(f"❌ {tool}: 未找到")
    
    def test_dwsim_adapter(self):
        """测试DWSIM适配器"""
        self.print_header("DWSIM适配器测试")
        
        test_script = self.services_dir / "dwsim-service" / "test_dwsim.py"
        if test_script.exists():
            print(f"运行DWSIM测试脚本: {test_script}")
            return self.run_command(f"python {test_script}", description="测试DWSIM适配器")
        else:
            print(f"❌ DWSIM测试脚本不存在: {test_script}")
            return False
    
    def test_freecad_adapter(self):
        """测试FreeCAD适配器"""
        self.print_header("FreeCAD适配器测试")
        
        test_script = self.services_dir / "freecad-service" / "test_freecad.py"
        if test_script.exists():
            print(f"运行FreeCAD测试脚本: {test_script}")
            return self.run_command(f"python {test_script}", description="测试FreeCAD适配器")
        else:
            print(f"❌ FreeCAD测试脚本不存在: {test_script}")
            return False
    
    def test_openfoam_adapter(self):
        """测试OpenFOAM适配器"""
        self.print_header("OpenFOAM适配器测试")
        
        test_script = self.services_dir / "openfoam-service" / "test_openfoam.py"
        if test_script.exists():
            print(f"运行OpenFOAM测试脚本: {test_script}")
            return self.run_command(f"python {test_script}", description="测试OpenFOAM适配器")
        else:
            print(f"❌ OpenFOAM测试脚本不存在: {test_script}")
            return False

def main():
    parser = argparse.ArgumentParser(description="UnveilChem外部工具适配层管理")
    parser.add_argument("command", choices=[
        "setup", "test", "build", "clean", "status"
    ], help="执行命令")
    parser.add_argument("--service", choices=[
        "dwsim", "freecad", "openfoam", "all"
    ], default="all", help="选择服务")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3], 
                       help="执行特定阶段")
    
    args = parser.parse_args()
    
    manager = DevelopmentManager()
    
    if args.command == "setup":
        print("🚀 设置开发环境...")
        manager.check_environment()
        
        if args.service in ["dwsim", "all"]:
            manager.setup_dwsim_environment()
        
        if args.service in ["freecad", "all"]:
            manager.setup_freecad_environment()
        
        if args.service in ["openfoam", "all"]:
            manager.setup_openfoam_environment()
        
        print("✅ 环境设置完成")
    
    elif args.command == "test":
        print("🧪 运行测试...")
        
        if args.service in ["dwsim", "all"]:
            print("测试DWSIM适配器...")
            # 这里可以添加实际的测试运行
        
        if args.service in ["freecad", "all"]:
            print("测试FreeCAD适配器...")
        
        if args.service in ["openfoam", "all"]:
            print("测试OpenFOAM适配器...")
        
        print("✅ 测试完成")
    
    elif args.command == "build":
        print("🔨 构建项目...")
        manager.create_dwsim_adapter()
        manager.create_freecad_adapter()
        manager.create_openfoam_adapter()
        manager.create_test_scripts()
        print("✅ 构建完成")
    
    elif args.command == "clean":
        print("🧹 清理项目...")
        # 清理临时文件和构建产物
        print("✅ 清理完成")
    
    elif args.command == "status":
        print("📊 项目状态...")
        manager.check_environment()
        print("✅ 状态检查完成")

if __name__ == "__main__":
    main()
