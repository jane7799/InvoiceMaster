"""
日志管理模块
"""
import os
import platform
import logging
from logging.handlers import RotatingFileHandler


class LogManager:
    """日志管理器"""
    
    @staticmethod
    def get_log_directory():
        """获取跨平台日志目录"""
        system = platform.system()
        if system == "Windows":
            base = os.environ.get('APPDATA', os.path.expanduser('~'))
            return os.path.join(base, 'InvoiceMaster', 'logs')
        elif system == "Darwin":  # macOS
            return os.path.expanduser('~/Library/Logs/InvoiceMaster')
        else:  # Linux/UOS
            return os.path.expanduser('~/.local/share/InvoiceMaster/logs')
    
    @staticmethod
    def setup_logging():
        """配置日志系统"""
        try:
            # 创建日志目录
            log_dir = LogManager.get_log_directory()
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, 'invoice_master.log')
            
            # 文件处理器（带轮转）
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10 MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)
            
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            
            # 设置格式
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # 配置根日志记录器
            logger = logging.getLogger()
            logger.setLevel(logging.INFO)
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            
            return logger
        except Exception as e:
            print(f"日志系统初始化失败: {e}")
            return logging.getLogger()
