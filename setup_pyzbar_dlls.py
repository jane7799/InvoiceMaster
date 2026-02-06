#!/usr/bin/env python3
"""
pyzbar DLL 安装检查和修复脚本
在 Windows 上运行此脚本来检查和修复 pyzbar DLL 问题

使用方法:
    python setup_pyzbar_dlls.py
"""

import os
import sys
import shutil
import urllib.request
import zipfile
import tempfile

def find_pyzbar_dlls():
    """查找 pyzbar 需要的 DLL 文件"""
    try:
        import pyzbar
        pyzbar_dir = os.path.dirname(pyzbar.__file__)
        print(f"[信息] pyzbar 安装位置: {pyzbar_dir}")
        
        required_dlls = ['libiconv.dll', 'libzbar-64.dll']
        found = []
        missing = []
        
        for dll in required_dlls:
            dll_path = os.path.join(pyzbar_dir, dll)
            if os.path.exists(dll_path):
                found.append((dll, dll_path))
            else:
                missing.append(dll)
        
        # 也检查其他可能的位置
        other_paths = [
            os.path.join(sys.prefix, 'Library', 'bin'),
            os.path.join(sys.prefix, 'Scripts'),
            os.path.join(os.environ.get('CONDA_PREFIX', ''), 'Library', 'bin'),
        ]
        
        for path in other_paths:
            if os.path.exists(path):
                for dll in missing[:]:  # 使用副本迭代
                    dll_path = os.path.join(path, dll)
                    if os.path.exists(dll_path):
                        found.append((dll, dll_path))
                        missing.remove(dll)
        
        return pyzbar_dir, found, missing
    except ImportError:
        print("[错误] pyzbar 未安装，请先运行: pip install pyzbar")
        return None, [], []

def download_zbar_dlls(target_dir):
    """从官方源下载 zbar DLL 文件"""
    print("[信息] 正在下载 zbar DLL 文件...")
    
    # 下载预编译的 zbar DLL
    # 注意：这是一个示例 URL，实际使用时需要确保是有效的
    urls = [
        # 64位 DLL
        ("https://github.com/NaturalHistoryMuseum/pyzbar/raw/v0.1.9/pyzbar/libzbar-64.dll", "libzbar-64.dll"),
        ("https://github.com/NaturalHistoryMuseum/pyzbar/raw/v0.1.9/pyzbar/libiconv.dll", "libiconv.dll"),
    ]
    
    for url, filename in urls:
        target_path = os.path.join(target_dir, filename)
        if not os.path.exists(target_path):
            try:
                print(f"  正在下载 {filename}...")
                urllib.request.urlretrieve(url, target_path)
                print(f"  已保存到 {target_path}")
            except Exception as e:
                print(f"  [警告] 下载 {filename} 失败: {e}")
                print(f"  请手动下载并放置到 {target_dir}")

def test_pyzbar():
    """测试 pyzbar 是否正常工作"""
    print("\n[测试] 正在测试 pyzbar...")
    try:
        from pyzbar.pyzbar import decode
        print("[成功] pyzbar 可以正常导入!")
        return True
    except ImportError as e:
        print(f"[失败] pyzbar 导入失败: {e}")
        return False
    except Exception as e:
        print(f"[失败] pyzbar 测试失败: {e}")
        return False

def main():
    print("=" * 60)
    print("pyzbar DLL 检查和修复工具")
    print("=" * 60)
    
    if sys.platform != 'win32':
        print("[信息] 此脚本仅适用于 Windows 系统")
        print("[信息] macOS/Linux 通常不需要这些 DLL 文件")
        return
    
    # 检查 DLL
    pyzbar_dir, found, missing = find_pyzbar_dlls()
    
    if pyzbar_dir is None:
        return
    
    print(f"\n[已找到的 DLL]")
    for dll, path in found:
        print(f"  ✓ {dll}: {path}")
    
    if missing:
        print(f"\n[缺失的 DLL]")
        for dll in missing:
            print(f"  ✗ {dll}")
        
        print(f"\n[修复建议]")
        print("1. 尝试重新安装 pyzbar:")
        print("   pip uninstall pyzbar && pip install pyzbar")
        print("")
        print("2. 或者手动下载 DLL 文件并放入:")
        print(f"   {pyzbar_dir}")
        print("")
        
        # 尝试自动下载
        response = input("是否尝试自动下载缺失的 DLL? [y/N]: ").strip().lower()
        if response == 'y':
            download_zbar_dlls(pyzbar_dir)
    else:
        print("\n[信息] 所有必需的 DLL 文件都已存在")
    
    # 最终测试
    print("\n" + "=" * 60)
    if test_pyzbar():
        print("\n[结论] pyzbar 已正确配置，可以进行打包")
        print("运行以下命令进行打包:")
        print("  pyinstaller InvoiceMaster.spec")
    else:
        print("\n[结论] pyzbar 仍有问题，请检查以下事项:")
        print("1. 确保已安装 Visual C++ Redistributable 2019 或更新版本")
        print("2. 确保 DLL 文件与 Python 架构匹配 (x64/x86)")
        print("3. 尝试使用 Dependency Walker 检查 DLL 依赖")

if __name__ == "__main__":
    main()
