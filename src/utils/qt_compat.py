"""
PyQt5/PyQt6 兼容性 Shim 层
如果在导入 PyQt6 时失败，或者在 Windows 7 等不支持 PyQt6 的环境下，
本模块会自动使用 PyQt5 模拟 PyQt6 接口，从而不需要修改现有业务代码。
"""

import sys
import types
import logging
import platform

logger = logging.getLogger(__name__)

# 是否强制使用 PyQt5 (例如在 Win7 下)
force_pyqt5 = False
if platform.system() == 'Windows':
    win_ver = platform.release()
    if win_ver == '7':
        force_pyqt5 = True
        logger.info("Windows 7 检测到，强制启用 PyQt5 兼容层")

# 检查 PyQt6 是否可用
pyqt6_available = False
if not force_pyqt5:
    try:
        import PyQt6
        pyqt6_available = True
    except ImportError:
        logger.info("未检测到 PyQt6，尝试载入 PyQt5 兼容层")

if not pyqt6_available:
    # 尝试导入 PyQt5
    try:
        import PyQt5
        import PyQt5.QtCore
        import PyQt5.QtGui
        import PyQt5.QtWidgets
        import PyQt5.QtPrintSupport
        try:
            import PyQt5.sip as sip
        except ImportError:
            import sip
    except ImportError as e:
        # 如果 PyQt5 和 PyQt6 都不存在，日志记录后抛出
        logger.error("PyQt6 和 PyQt5 均不可用！")
        raise e

    # ═══════════════════════════════════════════════════════════════════════════
    # 1. 模拟 Qt.AspectRatioMode 等命名空间 (PyQt6 风格)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # 包装 Qt 对象，使其支持 PyQt6 的命名空间（如 Qt.AlignmentFlag.AlignCenter）
    class QtProxy:
        def __init__(self, real_qt):
            self._real_qt = real_qt
            
        def __getattr__(self, name):
            if hasattr(self._real_qt, name):
                return getattr(self._real_qt, name)
            # 返回一个代理，允许任意 of the sub-attributes, e.g., Qt.AlignmentFlag.AlignCenter -> Qt.AlignCenter
            return NamespaceProxy(self._real_qt, name)

    class NamespaceProxy:
        def __init__(self, real_qt, namespace_name):
            self._real_qt = real_qt
            self._namespace_name = namespace_name
            
        def __getattr__(self, name):
            if hasattr(self._real_qt, name):
                return getattr(self._real_qt, name)
            raise AttributeError(f"PyQt5.QtCore.Qt has no attribute '{name}' (in namespace '{self._namespace_name}')")

    # ═══════════════════════════════════════════════════════════════════════════
    # 2. 模拟模块和类成员的特定差异
    # ═══════════════════════════════════════════════════════════════════════════
    
    # PyQt5 QDialog / QMenu / QApplication 等类在旧版本中没有 exec，统一添加别名
    for cls_name in ['QDialog', 'QMenu', 'QApplication', 'QDrag']:
        if hasattr(PyQt5.QtWidgets, cls_name):
            cls = getattr(PyQt5.QtWidgets, cls_name)
            if not hasattr(cls, 'exec') and hasattr(cls, 'exec_'):
                cls.exec = cls.exec_
                
    for cls_name in ['QThread', 'QCoreApplication', 'QEventLoop']:
        if hasattr(PyQt5.QtCore, cls_name):
            cls = getattr(PyQt5.QtCore, cls_name)
            if not hasattr(cls, 'exec') and hasattr(cls, 'exec_'):
                cls.exec = cls.exec_

    # 模拟 QPrinter.ColorMode / DuplexMode / PrinterMode 等
    class PrinterColorMode:
        Color = PyQt5.QtPrintSupport.QPrinter.Color
        GrayScale = PyQt5.QtPrintSupport.QPrinter.GrayScale

    class PrinterDuplexMode:
        DuplexNone = PyQt5.QtPrintSupport.QPrinter.DuplexNone
        DuplexLongSide = PyQt5.QtPrintSupport.QPrinter.DuplexLongSide
        DuplexShortSide = PyQt5.QtPrintSupport.QPrinter.DuplexShortSide

    class PrinterMode:
        ScreenResolution = PyQt5.QtPrintSupport.QPrinter.ScreenResolution
        PrinterResolution = PyQt5.QtPrintSupport.QPrinter.PrinterResolution
        HighResolution = PyQt5.QtPrintSupport.QPrinter.HighResolution

    class PrinterUnit:
        DevicePixel = PyQt5.QtPrintSupport.QPrinter.DevicePixel
        Millimeter = PyQt5.QtPrintSupport.QPrinter.Millimeter
        Point = PyQt5.QtPrintSupport.QPrinter.Point
        Inch = PyQt5.QtPrintSupport.QPrinter.Inch

    PyQt5.QtPrintSupport.QPrinter.ColorMode = PrinterColorMode
    PyQt5.QtPrintSupport.QPrinter.DuplexMode = PrinterDuplexMode
    PyQt5.QtPrintSupport.QPrinter.PrinterMode = PrinterMode
    PyQt5.QtPrintSupport.QPrinter.Unit = PrinterUnit

    # 模拟 QPageLayout.Orientation
    class PageLayoutOrientation:
        Portrait = PyQt5.QtGui.QPageLayout.Portrait
        Landscape = PyQt5.QtGui.QPageLayout.Landscape

    PyQt5.QtGui.QPageLayout.Orientation = PageLayoutOrientation

    # 模拟 QEasingCurve.Type
    class EasingCurveType:
        Linear = PyQt5.QtCore.QEasingCurve.Linear
        InOutSine = PyQt5.QtCore.QEasingCurve.InOutSine
        OutQuad = PyQt5.QtCore.QEasingCurve.OutQuad
        
    PyQt5.QtCore.QEasingCurve.Type = EasingCurveType

    # 模拟 QPainter.RenderHint
    class PainterRenderHint:
        Antialiasing = PyQt5.QtGui.QPainter.Antialiasing
        TextAntialiasing = PyQt5.QtGui.QPainter.TextAntialiasing
        SmoothPixmapTransform = PyQt5.QtGui.QPainter.SmoothPixmapTransform
        NonCosmeticDefaultPen = PyQt5.QtGui.QPainter.NonCosmeticDefaultPen

    PyQt5.QtGui.QPainter.RenderHint = PainterRenderHint

    # ═══════════════════════════════════════════════════════════════════════════
    # 3. 拦截 sys.modules 中的 PyQt6 导入并重定向到 PyQt5
    # ═══════════════════════════════════════════════════════════════════════════
    
    # 模拟 PyQt6.QtCore 模块
    class PyQt6QtCoreModule(types.ModuleType):
        def __init__(self):
            super().__init__('PyQt6.QtCore')
            
        def __getattr__(self, name):
            if name == 'Qt':
                return QtProxy(PyQt5.QtCore.Qt)
            if hasattr(PyQt5.QtCore, name):
                return getattr(PyQt5.QtCore, name)
            raise AttributeError(f"module 'PyQt6.QtCore' has no attribute '{name}'")
            
        def __dir__(self):
            return list(set(dir(PyQt5.QtCore) + ['Qt']))

    # 模拟 PyQt6.QtGui 模块 (处理移动到 QtWidgets 的 QAction, QShortcut 等)
    class PyQt6QtGuiModule(types.ModuleType):
        def __init__(self):
            super().__init__('PyQt6.QtGui')
            
        def __getattr__(self, name):
            if hasattr(PyQt5.QtGui, name):
                return getattr(PyQt5.QtGui, name)
            if hasattr(PyQt5.QtWidgets, name):
                return getattr(PyQt5.QtWidgets, name)
            raise AttributeError(f"module 'PyQt6.QtGui' has no attribute '{name}'")
            
        def __dir__(self):
            return list(set(dir(PyQt5.QtGui) + dir(PyQt5.QtWidgets)))

    # 模拟 PyQt6.QtWidgets 模块
    class PyQt6QtWidgetsModule(types.ModuleType):
        def __init__(self):
            super().__init__('PyQt6.QtWidgets')
            
        def __getattr__(self, name):
            if hasattr(PyQt5.QtWidgets, name):
                return getattr(PyQt5.QtWidgets, name)
            if hasattr(PyQt5.QtGui, name):
                return getattr(PyQt5.QtGui, name)
            raise AttributeError(f"module 'PyQt6.QtWidgets' has no attribute '{name}'")
            
        def __dir__(self):
            return list(set(dir(PyQt5.QtWidgets) + dir(PyQt5.QtGui)))

    # 模拟 PyQt6.QtPrintSupport 模块
    class PyQt6QtPrintSupportModule(types.ModuleType):
        def __init__(self):
            super().__init__('PyQt6.QtPrintSupport')
            
        def __getattr__(self, name):
            if hasattr(PyQt5.QtPrintSupport, name):
                return getattr(PyQt5.QtPrintSupport, name)
            raise AttributeError(f"module 'PyQt6.QtPrintSupport' has no attribute '{name}'")
            
        def __dir__(self):
            return dir(PyQt5.QtPrintSupport)

    # 模拟父包 PyQt6
    class PyQt6Module(types.ModuleType):
        def __init__(self):
            super().__init__('PyQt6')
            
        def __getattr__(self, name):
            if name == 'QtCore': return sys.modules['PyQt6.QtCore']
            if name == 'QtGui': return sys.modules['PyQt6.QtGui']
            if name == 'QtWidgets': return sys.modules['PyQt6.QtWidgets']
            if name == 'QtPrintSupport': return sys.modules['PyQt6.QtPrintSupport']
            if name == 'sip': return sys.modules['PyQt6.sip']
            raise AttributeError(f"module 'PyQt6' has no attribute '{name}'")

    # 注入到 sys.modules 中，拦截所有的 import PyQt6 动作
    sys.modules['PyQt6.QtCore'] = PyQt6QtCoreModule()
    sys.modules['PyQt6.QtGui'] = PyQt6QtGuiModule()
    sys.modules['PyQt6.QtWidgets'] = PyQt6QtWidgetsModule()
    sys.modules['PyQt6.QtPrintSupport'] = PyQt6QtPrintSupportModule()
    sys.modules['PyQt6.sip'] = sip
    sys.modules['PyQt6'] = PyQt6Module()

    logger.info("已成功激活 PyQt5 -> PyQt6 兼容注入层")
