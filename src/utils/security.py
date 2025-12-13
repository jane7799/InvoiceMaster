"""
安全模块
提供输入验证和安全工具
"""
import os
import re
import logging
from typing import List, Optional

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}

# 危险路径模式
DANGEROUS_PATH_PATTERNS = [
    r'\.\.',           # 目录遍历
    r'^/',             # 绝对路径到根
    r'^~',             # 用户目录引用
    r'[<>:"|?*]',      # Windows 非法字符
]


class SecurityValidator:
    """安全验证器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_file_path(self, file_path: str) -> tuple:
        """
        验证文件路径安全性
        
        Args:
            file_path: 文件路径
            
        Returns:
            (is_valid: bool, error_message: str)
        """
        if not file_path:
            return False, "文件路径不能为空"
        
        # 规范化路径
        normalized = os.path.normpath(file_path)
        
        # 检查目录遍历
        if '..' in normalized:
            self.logger.warning(f"检测到目录遍历尝试: {file_path}")
            return False, "不允许的路径格式"
        
        # 检查文件是否存在
        if not os.path.exists(normalized):
            return False, "文件不存在"
        
        # 检查是否为文件
        if not os.path.isfile(normalized):
            return False, "路径不是文件"
        
        # 检查扩展名
        ext = os.path.splitext(normalized)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"不支持的文件类型: {ext}"
        
        return True, ""
    
    def validate_file_list(self, file_paths: List[str]) -> tuple:
        """
        验证文件列表
        
        Returns:
            (valid_files: List[str], invalid_files: List[tuple])
        """
        valid = []
        invalid = []
        
        for fp in file_paths:
            is_valid, error = self.validate_file_path(fp)
            if is_valid:
                valid.append(fp)
            else:
                invalid.append((fp, error))
        
        return valid, invalid
    
    def sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除危险字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            安全的文件名
        """
        if not filename:
            return "unnamed"
        
        # 移除路径分隔符
        filename = os.path.basename(filename)
        
        # 移除危险字符
        safe_chars = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # 限制长度
        if len(safe_chars) > 200:
            name, ext = os.path.splitext(safe_chars)
            safe_chars = name[:200-len(ext)] + ext
        
        return safe_chars or "unnamed"
    
    def validate_api_key(self, api_key: str) -> bool:
        """
        验证 API Key 格式
        
        Args:
            api_key: API Key 字符串
            
        Returns:
            是否有效
        """
        if not api_key:
            return False
        
        # 百度 API Key 通常是 24 字符的字母数字
        if not re.match(r'^[a-zA-Z0-9]{16,64}$', api_key):
            return False
        
        return True
    
    def validate_url(self, url: str) -> tuple:
        """
        验证 URL 安全性
        
        Returns:
            (is_valid: bool, error_message: str)
        """
        if not url:
            return True, ""  # 空 URL 是允许的（未配置）
        
        # 检查协议
        if not url.startswith(('http://', 'https://')):
            return False, "URL 必须以 http:// 或 https:// 开头"
        
        # 检查本地地址（允许）
        local_patterns = ['localhost', '127.0.0.1', '192.168.', '10.', '172.']
        if any(p in url for p in local_patterns):
            return True, ""
        
        # 外部 URL 应该使用 HTTPS
        if url.startswith('http://') and not any(p in url for p in local_patterns):
            self.logger.warning(f"外部 URL 使用不安全的 HTTP: {url}")
            return False, "外部服务 URL 应使用 HTTPS"
        
        return True, ""


# 全局验证器实例
validator = SecurityValidator()


def validate_file(file_path: str) -> tuple:
    """便捷函数：验证单个文件"""
    return validator.validate_file_path(file_path)


def validate_files(file_paths: List[str]) -> tuple:
    """便捷函数：验证文件列表"""
    return validator.validate_file_list(file_paths)


def sanitize_filename(filename: str) -> str:
    """便捷函数：清理文件名"""
    return validator.sanitize_filename(filename)
