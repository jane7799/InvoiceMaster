"""
PyInstaller 运行时钩子

此脚本在主程序（InvoiceMaster.py）之前由 PyInstaller 引导程序自动执行。
主要职责：
  1. 将 _MEIPASS 及其子目录加入 DLL 搜索路径
  2. 设置 Qt 插件路径环境变量
"""

import os
import sys

# PyInstaller 会将 _MEIPASS 设置为临时解压目录
if hasattr(sys, '_MEIPASS'):
    base = sys._MEIPASS

    # ── 1. 将 _MEIPASS 加入 PATH（确保所有 DLL 可被找到）─────────────
    existing_path = os.environ.get('PATH', '')
    os.environ['PATH'] = base + os.pathsep + existing_path

    # ── 2. 设置 Qt 插件路径 ────────────────────────────────────────────
    # 兼容 PyQt6 和 PyQt5
    qt_plugins = os.path.join(base, 'PyQt6', 'Qt6', 'plugins')
    if not os.path.exists(qt_plugins):
        # 探测 PyQt5 插件路径
        qt_plugins = os.path.join(base, 'PyQt5', 'Qt5', 'plugins')
        if not os.path.exists(qt_plugins):
            qt_plugins = os.path.join(base, 'PyQt5', 'plugins')

    if os.path.exists(qt_plugins):
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(
            qt_plugins, 'platforms'
        )

    # ── 3. 使用 os.add_dll_directory()（Python 3.8+ / Windows 10+）───
    if sys.version_info >= (3, 8) and hasattr(os, 'add_dll_directory'):
        # 添加根目录
        try:
            os.add_dll_directory(base)
        except OSError:
            pass

        # 添加可能包含 DLL 的子目录
        dll_subdirs = [
            'pyzbar', 'cv2', 
            'PyQt6', 'PyQt6/Qt6/bin',
            'PyQt5', 'PyQt5/Qt5/bin', 'PyQt5/Qt/bin'
        ]
        for subdir in dll_subdirs:
            d = os.path.join(base, subdir)
            if os.path.isdir(d):
                try:
                    os.add_dll_directory(d)
                except OSError:
                    pass

    # ── 4. 将所有子目录也追加到 PATH（兜底方案）────────────────────────
    dll_paths = ['pyzbar', 'cv2', 'PyQt6', 'PyQt6/Qt6/bin', 'PyQt5', 'PyQt5/Qt5/bin', 'PyQt5/Qt/bin']
    for subdir in dll_paths:
        d = os.path.join(base, subdir)
        if os.path.isdir(d) and d not in os.environ['PATH']:
            os.environ['PATH'] = d + os.pathsep + os.environ['PATH']
