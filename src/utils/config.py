
import platform

def _detect_platform():
    s = platform.system()
    if s == "Darwin": return "mac"
    if s == "Windows":
        v = platform.release()
        if v == "7": return "win7"
        return "win10"
    return "linux"

PLATFORM = _detect_platform()

UI_CONFIG = {
    "use_gradients": True,
    "shadow_blur": 25, 
    "shadow_opacity": 25,
    "is_legacy": False,
    "preview_render_scale": 4.0 if PLATFORM == "mac" else 2.0
}

# Win7 legacy mode handling
if PLATFORM == "win7":
    UI_CONFIG.update({
        "use_gradients": False,
        "shadow_blur": 0,
        "shadow_opacity": 0,
        "is_legacy": True
    })
