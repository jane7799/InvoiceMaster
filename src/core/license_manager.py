"""
授权管理模块
提供机器码生成、激活码验证、试用次数管理等功能
"""
import hashlib
import hmac
import uuid
import platform
from PyQt6.QtCore import QSettings

# 密钥：用于生成和验证激活码（请妥善保管，不要泄露）
SECRET_KEY = "InvoiceMaster2024SecretKey#@!"

class LicenseManager:
    """授权管理器"""
    
    def __init__(self):
        self.settings = QSettings("MySoft", "InvoiceMaster")
        self.machine_code = self._get_or_generate_machine_code()
    
    def _get_hardware_info(self):
        """获取硬件信息（跨平台）"""
        try:
            system = platform.system()
            
            if system == "Windows":
                # Windows: 使用 UUID + 计算机名
                import subprocess
                try:
                    # 获取主板序列号
                    output = subprocess.check_output("wmic csproduct get uuid", shell=True).decode()
                    uuid_str = output.split('\n')[1].strip()
                except Exception:
                    uuid_str = str(uuid.getnode())
                
                computer_name = platform.node()
                return f"{uuid_str}-{computer_name}"
            
            elif system == "Darwin":  # macOS
                # macOS: 使用硬件UUID
                import subprocess
                try:
                    output = subprocess.check_output(
                        ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"]
                    ).decode()
                    for line in output.split('\n'):
                        if 'IOPlatformUUID' in line:
                            uuid_str = line.split('"')[3]
                            return uuid_str
                except Exception:
                    pass
                # 备用方案：MAC地址
                return str(uuid.getnode())
            
            else:  # Linux/UOS
                # Linux: 使用 machine-id
                try:
                    with open('/etc/machine-id', 'r') as f:
                        return f.read().strip()
                except Exception:
                    try:
                        with open('/var/lib/dbus/machine-id', 'r') as f:
                            return f.read().strip()
                    except Exception:
                        # 备用方案：MAC地址
                        return str(uuid.getnode())
        
        except Exception as e:
            # 最终备用方案
            return str(uuid.getnode())
    
    def _generate_machine_code(self, hardware_info):
        """根据硬件信息生成机器码"""
        # 使用 SHA256 哈希
        hash_obj = hashlib.sha256(hardware_info.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        
        # 取前16位，格式化为 XXXX-XXXX-XXXX-XXXX
        code = hash_hex[:16].upper()
        return f"{code[0:4]}-{code[4:8]}-{code[8:12]}-{code[12:16]}"
    
    def _get_or_generate_machine_code(self):
        """获取或生成机器码"""
        # 先尝试从配置中读取
        saved_code = self.settings.value("machine_code", "")
        if saved_code:
            return saved_code
        
        # 如果没有，则生成新的机器码
        hardware_info = self._get_hardware_info()
        machine_code = self._generate_machine_code(hardware_info)
        
        # 保存到配置
        self.settings.setValue("machine_code", machine_code)
        return machine_code
    
    def get_machine_code(self):
        """获取机器码"""
        return self.machine_code
    
    def verify_activation_code(self, activation_code):
        """验证激活码是否正确"""
        try:
            # 移除激活码中的连字符和空格,转为大写
            activation_code = activation_code.replace("-", "").replace(" ", "").strip().upper()
            
            # 使用 HMAC-SHA256 生成签名
            message = self.machine_code.encode('utf-8')
            signature = hmac.new(
                SECRET_KEY.encode('utf-8'),
                message,
                hashlib.sha256
            ).hexdigest()
            
            # 取前16位
            expected_code = signature[:16].upper()
            
            # 调试信息(帮助排查激活问题)
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"激活验证 - 机器码: {self.machine_code}")
            logger.info(f"激活验证 - 期望激活码: {expected_code}")
            logger.info(f"激活验证 - 输入激活码: {activation_code}")
            logger.info(f"激活验证 - 匹配结果: {activation_code == expected_code}")
            
            # 比较
            return activation_code == expected_code
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"激活码验证异常: {str(e)}", exc_info=True)
            return False
    
    def activate(self, activation_code):
        """激活软件"""
        if self.verify_activation_code(activation_code):
            # 保存激活码和激活状态
            self.settings.setValue("activation_code", activation_code)
            self.settings.setValue("is_activated", True)
            return True
        return False
    
    def is_activated(self):
        """检查是否已激活"""
        return self.settings.value("is_activated", False, type=bool)
    
    def get_trial_count(self):
        """获取已使用的试用次数"""
        return self.settings.value("trial_count", 0, type=int)
    
    def increment_trial_count(self):
        """增加试用次数"""
        current_count = self.get_trial_count()
        self.settings.setValue("trial_count", current_count + 1)
        return current_count + 1
    
    def get_remaining_trials(self):
        """获取剩余试用次数"""
        return max(0, 10 - self.get_trial_count())
    
    def can_use_feature(self):
        """检查是否可以使用功能（已激活或还有试用次数）"""
        if self.is_activated():
            return True, "已激活"
        
        remaining = self.get_remaining_trials()
        if remaining > 0:
            return True, f"试用中，剩余 {remaining} 次"
        
        return False, "试用次数已用完，请激活"
    
    def reset_trial(self):
        """重置试用次数（仅用于测试）"""
        self.settings.setValue("trial_count", 0)
    
    def get_activation_info(self):
        """获取激活信息摘要"""
        info = {
            "machine_code": self.machine_code,
            "is_activated": self.is_activated(),
            "trial_count": self.get_trial_count(),
            "remaining_trials": self.get_remaining_trials()
        }
        return info
