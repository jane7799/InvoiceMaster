"""
配置管理模块
"""
import os
import sys
import platform


# 全局配置
APP_VERSION = "V1.0.2"
APP_NAME = "智能发票打印助手"
APP_AUTHOR_CN = "© 会钓鱼的猫"


def _detect_platform():
    """检测平台并返回 UI 配置"""
    system = platform.system()
    
    # 默认配置（现代平台）
    config = {
        "use_animations": True,
        "use_gradients": True,
        "shadow_blur": 25,
        "shadow_opacity": 25,
        "is_legacy": False,
        "platform_name": system,
        "preview_render_scale": 6.0  # 现代系统使用最高分辨率预览
    }
    
    if system == "Windows":
        try:
            ver = sys.getwindowsversion()
            # Win7: major=6, minor=1
            # Win10: major=10
            if ver.major == 6 and ver.minor <= 1:
                # Windows 7 或更早版本 - 降低内存占用
                config.update({
                    "use_animations": False,
                    "use_gradients": False,
                    "shadow_blur": 10,
                    "shadow_opacity": 15,
                    "is_legacy": True,
                    "platform_name": "Windows 7",
                    "preview_render_scale": 4.0  # Win7 最低分辨率
                })
            else:
                config["platform_name"] = "Windows 10+"
        except:
            pass
    elif system == "Linux":
        # 统信等 Linux 系统 - 中等配置
        config.update({
            "use_animations": True,
            "use_gradients": True,
            "shadow_blur": 15,
            "shadow_opacity": 20,
            "platform_name": "Linux/UOS",
            "preview_render_scale": 5.0  # Linux 使用中等分辨率
        })
    
    return config


# 初始化平台配置
UI_CONFIG = _detect_platform()


def resource_path(relative_path):
    """获取资源文件的绝对路径"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
