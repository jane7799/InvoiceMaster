#!/usr/bin/env python3
"""
获取当前系统的真实机器码
"""
import hashlib
import uuid
import platform
from PyQt6.QtCore import QSettings

def get_hardware_info():
    """获取硬件信息（跨平台）"""
    try:
        system = platform.system()
        
        if system == "Darwin":  # macOS
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
            except:
                pass
            # 备用方案：MAC地址
            return str(uuid.getnode())
        
        else:
            # 备用方案
            return str(uuid.getnode())
    
    except Exception as e:
        # 最终备用方案
        return str(uuid.getnode())

def generate_machine_code(hardware_info):
    """根据硬件信息生成机器码"""
    # 使用 SHA256 哈希
    hash_obj = hashlib.sha256(hardware_info.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()
    
    # 取前16位，格式化为 XXXX-XXXX-XXXX-XXXX
    code = hash_hex[:16].upper()
    return f"{code[0:4]}-{code[4:8]}-{code[8:12]}-{code[12:16]}"

if __name__ == "__main__":
    print("=" * 70)
    print("获取当前系统的机器码")
    print("=" * 70)
    print()
    
    # 检查QSettings中保存的机器码
    settings = QSettings("MySoft", "InvoiceMaster")
    saved_code = settings.value("machine_code", "")
    
    if saved_code:
        print(f"✅ 已保存的机器码: {saved_code}")
    else:
        print("⚠️  未找到已保存的机器码，正在生成新的...")
    
    print()
    
    # 获取硬件信息
    hardware_info = get_hardware_info()
    print(f"硬件信息: {hardware_info}")
    print()
    
    # 生成机器码
    machine_code = generate_machine_code(hardware_info)
    print(f"生成的机器码: {machine_code}")
    print()
    
    if saved_code and saved_code != machine_code:
        print("⚠️  警告：生成的机器码与保存的不一致！")
        print(f"   保存的: {saved_code}")
        print(f"   生成的: {machine_code}")
        print()
        print("   建议使用保存的机器码生成激活码")
    
    print("=" * 70)
