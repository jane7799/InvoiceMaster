"""
启动环境检查模块

在应用主窗口加载（导入 PyQt6）之前运行，检测常见的 Windows 兼容性问题：
- Windows 版本（Win7 不支持 PyQt6/Qt6）
- VC++ 运行时 DLL
- pyzbar / OpenCV / PyMuPDF 依赖 DLL

所有用户可见的提示均使用中文，通过 ctypes MessageBox 显示（不依赖 Qt）。
"""

import sys
import os
import platform
import logging
import ctypes

logger = logging.getLogger(__name__)

# ─── Windows MessageBox 常量 ───────────────────────────────────────────────
MB_OK = 0x00000000
MB_ICONWARNING = 0x00000030
MB_ICONERROR = 0x00000010


# ═══════════════════════════════════════════════════════════════════════════
# 原生消息框（不依赖 Qt）
# ═══════════════════════════════════════════════════════════════════════════

def show_native_error(title: str, message: str, *, icon=MB_ICONWARNING):
    """使用 Windows 原生 MessageBox 显示错误（不依赖 Qt）。

    在非 Windows 平台上回退到 stderr 输出。
    """
    if platform.system() == 'Windows':
        try:
            ctypes.windll.user32.MessageBoxW(0, message, title, MB_OK | icon)
            return
        except Exception:
            pass
    # 非 Windows 或调用失败时回退到控制台输出
    print(f"[{title}] {message}", file=sys.stderr)


# ═══════════════════════════════════════════════════════════════════════════
# 环境检查
# ═══════════════════════════════════════════════════════════════════════════

def _check_windows_version() -> list[str]:
    """检查 Windows 版本，如果使用原生 PyQt6 在 Win7 下运行时给予提示。"""
    issues: list[str] = []
    if platform.system() != 'Windows':
        return issues

    win_ver = platform.release()  # "7", "10", "11", …
    logger.info(f"检测到 Windows 版本: {win_ver}")

    if win_ver == '7':
        # 检查是否正在使用原生 PyQt6（还是 PyQt5 兼容层）
        is_using_native_pyqt6 = True
        core_mod = sys.modules.get('PyQt6.QtCore')
        if core_mod and core_mod.__class__.__name__ == 'PyQt6QtCoreModule':
            is_using_native_pyqt6 = False

        if is_using_native_pyqt6:
            msg = (
                "当前系统为 Windows 7，当前运行的版本基于 PyQt6（Qt6），不支持 Windows 7。\n\n"
                "如果您遇到界面无法显示或报错，请运行「Win7兼容版」。\n"
                "程序将尝试继续运行。"
            )
            issues.append("Windows 7 运行原生 PyQt6，建议使用 Win7 兼容版")
            show_native_error("Windows 版本提示", msg, icon=MB_ICONWARNING)

    return issues


def _check_vcruntime() -> list[str]:
    """检查 VC++ 运行时是否可用（VCRUNTIME140.dll / MSVCP140.dll）。"""
    issues: list[str] = []
    if platform.system() != 'Windows':
        return issues

    required_dlls = ['VCRUNTIME140.dll', 'MSVCP140.dll']
    missing: list[str] = []

    for dll_name in required_dlls:
        try:
            ctypes.WinDLL(dll_name)
        except OSError:
            missing.append(dll_name)
            logger.warning(f"未找到 VC++ 运行时: {dll_name}")

    if missing:
        dll_list = '、'.join(missing)
        msg = (
            f"缺少 Microsoft Visual C++ 运行时组件：{dll_list}\n\n"
            "请从微软官网下载并安装 Visual C++ Redistributable：\n"
            "https://aka.ms/vs/17/release/vc_redist.x64.exe\n\n"
            "安装完成后请重新启动本程序。"
        )
        issues.append(f"缺少 VC++ 运行时: {dll_list}")
        show_native_error("运行时组件缺失", msg)

    return issues


def _fix_dll_search_paths() -> list[str]:
    """修复 PyInstaller 打包后的 DLL 搜索路径。

    主要处理 pyzbar 所需的 libzbar-64.dll / libiconv.dll。
    """
    issues: list[str] = []

    meipass = getattr(sys, '_MEIPASS', None)
    if meipass is None:
        # 非 PyInstaller 打包环境，无需修复
        return issues

    logger.info(f"PyInstaller 打包环境，_MEIPASS = {meipass}")

    # 需要添加到 DLL 搜索路径的子目录
    dll_dirs = [
        meipass,
        os.path.join(meipass, 'pyzbar'),
        os.path.join(meipass, 'cv2'),
        os.path.join(meipass, 'PyQt6'),
        os.path.join(meipass, 'PyQt6', 'Qt6', 'bin'),
    ]

    # 方式 1：os.add_dll_directory()（Python 3.8+ / Windows 10+）
    if sys.version_info >= (3, 8) and hasattr(os, 'add_dll_directory'):
        for d in dll_dirs:
            if os.path.isdir(d):
                try:
                    os.add_dll_directory(d)
                    logger.info(f"add_dll_directory: {d}")
                except OSError as e:
                    logger.warning(f"add_dll_directory 失败 ({d}): {e}")

    # 方式 2：同时追加 PATH（兼容旧版 Python / Win7）
    env_path = os.environ.get('PATH', '')
    additions = [d for d in dll_dirs if os.path.isdir(d) and d not in env_path]
    if additions:
        os.environ['PATH'] = os.pathsep.join(additions) + os.pathsep + env_path
        logger.info(f"PATH 已追加 {len(additions)} 个目录")

    # 验证关键 pyzbar DLL 是否可达
    pyzbar_dir = os.path.join(meipass, 'pyzbar')
    critical_dlls = ['libzbar-64.dll', 'libiconv.dll']
    for dll_name in critical_dlls:
        dll_path = os.path.join(pyzbar_dir, dll_name)
        if not os.path.exists(dll_path):
            # 也检查根目录
            dll_path_root = os.path.join(meipass, dll_name)
            if not os.path.exists(dll_path_root):
                logger.warning(f"pyzbar DLL 未找到: {dll_name}")
                issues.append(f"未找到 {dll_name}，二维码识别功能可能不可用")

    return issues


def check_environment() -> tuple[bool, list[str]]:
    """在应用启动前检查运行环境。

    Returns:
        (ok, error_messages): ok 为 True 表示环境正常，
        error_messages 包含所有检测到的问题描述。
    """
    issues: list[str] = []

    # 1. 检查 Windows 版本
    issues.extend(_check_windows_version())

    # 2. 检查 VC++ 运行时
    issues.extend(_check_vcruntime())

    # 3. 修复 DLL 搜索路径
    issues.extend(_fix_dll_search_paths())

    if issues:
        logger.warning(f"环境检查发现 {len(issues)} 个问题")
        for i, issue in enumerate(issues, 1):
            logger.warning(f"  [{i}] {issue}")
    else:
        logger.info("环境检查通过，未发现问题")

    return len(issues) == 0, issues


# ═══════════════════════════════════════════════════════════════════════════
# 安全导入包装器
# ═══════════════════════════════════════════════════════════════════════════

def safe_import_pyzbar():
    """安全导入 pyzbar，失败时返回 None。"""
    try:
        from pyzbar import pyzbar as _pyzbar
        logger.info("pyzbar 导入成功")
        return _pyzbar
    except Exception as e:
        logger.warning(f"pyzbar 导入失败: {e}")
        return None


def safe_import_cv2():
    """安全导入 OpenCV (cv2)，失败时返回 None。"""
    try:
        import cv2 as _cv2
        logger.info(f"OpenCV 导入成功，版本: {_cv2.__version__}")
        return _cv2
    except Exception as e:
        logger.warning(f"OpenCV 导入失败: {e}")
        return None


def safe_import_fitz():
    """安全导入 PyMuPDF (fitz)，失败时返回 None。"""
    try:
        import fitz as _fitz
        logger.info(f"PyMuPDF 导入成功，版本: {_fitz.version}")
        return _fitz
    except Exception as e:
        logger.warning(f"PyMuPDF 导入失败: {e}")
        return None
