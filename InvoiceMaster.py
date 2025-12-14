
import sys
import os
import platform
from PyQt6.QtWidgets import QApplication

# 确保 src 目录在 Python 路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.log_manager import LogManager
from src.utils.constants import APP_NAME, APP_VERSION
from src.ui.main_window import MainWindow
from src.ui.widgets import DynamicSplashScreen

if __name__ == "__main__":
    # 初始化日志系统
    logger = LogManager.setup_logging()
    logger.info("=" * 60)
    logger.info(f"应用启动 - {APP_NAME} {APP_VERSION}")
    logger.info(f"系统: {platform.system()} {platform.release()}")
    logger.info(f"Python: {sys.version.split()[0]}")
    logger.info(f"日志目录: {LogManager.get_log_directory()}")
    logger.info("=" * 60)
    
    # 全局异常处理
    def exception_hook(exc_type, exc_value, exc_traceback):
        logger.critical(
            "未捕获的异常",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = exception_hook
    
    try:
        app = QApplication(sys.argv)
        # 预加载资源或设置属性
        
        splash = DynamicSplashScreen()
        splash.show()
        
        # 创建主窗口
        # 使用 lambda 延迟显示主窗口，直到 splash 完成
        w = MainWindow()
        
        splash.finished.connect(lambda: [splash.close(), w.show()])
        
        logger.info("主窗口创建成功")
        exit_code = app.exec()
        logger.info(f"应用正常退出，退出码: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        logger.critical(f"应用启动失败: {str(e)}", exc_info=True)
        sys.exit(1)
