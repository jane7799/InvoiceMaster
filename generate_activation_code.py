#!/usr/bin/env python3
"""
激活码生成工具
用于根据用户的机器码生成对应的激活码

使用方法：
1. 交互式：python generate_activation_code.py
2. 命令行：python generate_activation_code.py A3F2-8B4C-D1E9-7A5B

注意：请妥善保管此脚本，不要分发给用户！
"""
import sys
import hashlib
import hmac

# 密钥：必须与客户端保持一致
SECRET_KEY = "InvoiceMaster2024SecretKey#@!"

def generate_activation_code(machine_code):
    """根据机器码生成激活码"""
    try:
        # 【关键修复】不要修改机器码格式,直接使用原始输入
        # 因为 license_manager.py 中验证时使用的是原始机器码(带连字符)
        machine_code = machine_code.strip()
        
        # 使用 HMAC-SHA256 生成签名
        message = machine_code.encode('utf-8')
        signature = hmac.new(
            SECRET_KEY.encode('utf-8'),
            message,
            hashlib.sha256
        ).hexdigest()
        
        # 取前16位,格式化为激活码
        code = signature[:16].upper()
        activation_code = f"{code[0:4]}-{code[4:8]}-{code[8:12]}-{code[12:16]}"
        
        return activation_code
    
    except Exception as e:
        return None

def main():
    print("=" * 60)
    print("智能发票管理助手 - 激活码生成工具")
    print("=" * 60)
    print()
    
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        machine_code = sys.argv[1]
    else:
        # 交互式输入
        print("请输入用户的机器码（格式：XXXX-XXXX-XXXX-XXXX）：")
        machine_code = input("> ").strip()
    
    if not machine_code:
        print("❌ 错误：机器码不能为空！")
        return
    
    # 生成激活码
    activation_code = generate_activation_code(machine_code)
    
    if activation_code:
        print()
        print("✅ 激活码生成成功！")
        print("-" * 60)
        print(f"机器码：{machine_code}")
        print(f"激活码：{activation_code}")
        print("-" * 60)
        print()
        print("请将激活码发送给用户。")
        print()
    else:
        print("❌ 错误：激活码生成失败，请检查机器码格式是否正确！")
    
    # 询问是否继续生成
    if len(sys.argv) <= 1:
        print()
        choice = input("是否继续生成其他激活码？(y/n): ").strip().lower()
        if choice == 'y':
            print()
            main()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已退出。")
    except Exception as e:
        print(f"\n❌ 发生错误：{e}")
