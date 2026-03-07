"""
检查 DWSIM python_packages 目录
"""
import os

dwsim_dir = r"C:\Users\54905\AppData\Local\DWSIM"
python_pkg_dir = os.path.join(dwsim_dir, "python_packages")

print(f"检查目录: {python_pkg_dir}")
print(f"存在: {os.path.exists(python_pkg_dir)}")

if os.path.exists(python_pkg_dir):
    print("\n目录内容:")
    for item in os.listdir(python_pkg_dir):
        item_path = os.path.join(python_pkg_dir, item)
        if os.path.isdir(item_path):
            print(f"  📁 {item}/")
        else:
            print(f"  📄 {item}")

# 检查是否有 DWSIM 相关的 DLL
print("\n\n搜索 DWSIM 目录下的 DLL:")
for root, dirs, files in os.walk(dwsim_dir):
    for f in files:
        if f.endswith('.dll') and 'DWSIM' in f:
            print(f"  {os.path.join(root, f)}")
    # 限制搜索深度
    if root.count(os.sep) > dwsim_dir.count(os.sep) + 2:
        break
