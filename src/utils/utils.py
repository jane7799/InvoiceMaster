
import sys
import os

def resource_path(relative_path):
    """获取资源文件的绝对路径 (支持 PyInstaller 打包)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
