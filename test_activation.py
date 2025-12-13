#!/usr/bin/env python3
"""
激活码测试工具 - 诊断激活失败问题
"""
import sys
import hashlib
import hmac

# 密钥
SECRET_KEY = "InvoiceMaster2024SecretKey#@!"

def test_activation(machine_code, activation_code):
    """测试激活码是否匹配"""
    print("=" * 70)
    print("激活码验证测试")
    print("=" * 70)
    print()
    
    # 显示输入
    print(f"机器码（原始）: {machine_code}")
    print(f"激活码（输入）: {activation_code}")
    print()
    
    # 移除激活码中的连字符
    activation_code_clean = activation_code.replace("-", "").strip()
    print(f"激活码（清理后）: {activation_code_clean}")
    print()
    
    # 使用机器码生成期望的激活码
    message = machine_code.encode('utf-8')
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message,
        hashlib.sha256
    ).hexdigest()
    
    expected_code = signature[:16].upper()
    
    print(f"HMAC签名（完整）: {signature}")
    print(f"期望激活码（前16位）: {expected_code}")
    print()
    
    # 比较
    match = activation_code_clean.upper() == expected_code
    
    print("-" * 70)
    if match:
        print("✅ 验证成功！激活码正确！")
    else:
        print("❌ 验证失败！激活码不匹配！")
        print()
        print(f"输入的激活码: {activation_code_clean.upper()}")
        print(f"期望的激活码: {expected_code}")
    print("-" * 70)
    print()
    
    return match

if __name__ == "__main__":
    # 从截图中看到的值
    machine_code = "1B53-4E7C-8A9D-F2B1"  # 请替换为实际机器码
    activation_code = "3848-1EA9-06D1-E4E8"  # 从截图中看到的激活码
    
    print("提示：如果机器码不正确，请手动修改脚本中的 machine_code 变量")
    print()
    
    test_activation(machine_code, activation_code)
    
    # 生成正确的激活码
    print()
    print("=" * 70)
    print("正确的激活码生成")
    print("=" * 70)
    message = machine_code.encode('utf-8')
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message,
        hashlib.sha256
    ).hexdigest()
    code = signature[:16].upper()
    correct_activation = f"{code[0:4]}-{code[4:8]}-{code[8:12]}-{code[12:16]}"
    print(f"机器码: {machine_code}")
    print(f"正确的激活码: {correct_activation}")
    print("=" * 70)
