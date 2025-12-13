"""
激活码生成Web服务
适用于NAS Docker部署
"""
from flask import Flask, render_template, request, jsonify
import hashlib
import hmac
import os

app = Flask(__name__)

# 从环境变量读取密钥，如果没有则使用默认值
SECRET_KEY = os.getenv('SECRET_KEY', 'InvoiceMaster2024SecretKey#@!')

def generate_activation_code(machine_code):
    """生成激活码"""
    try:
        # 【关键修复】只去除首尾空格,不要移除连字符!
        # 必须与 license_manager.py 中的验证逻辑保持一致
        machine_code = machine_code.strip()
        
        # 使用 HMAC-SHA256 生成签名
        message = machine_code.encode('utf-8')
        signature = hmac.new(
            SECRET_KEY.encode('utf-8'),
            message,
            hashlib.sha256
        ).hexdigest()
        
        # 取前16位并格式化
        code = signature[:16].upper()
        formatted_code = f"{code[0:4]}-{code[4:8]}-{code[8:12]}-{code[12:16]}"
        
        return formatted_code
    except Exception as e:
        return None

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """生成激活码API"""
    data = request.get_json()
    machine_code = data.get('machine_code', '')
    
    if not machine_code:
        return jsonify({'error': '请输入机器码'}), 400
    
    activation_code = generate_activation_code(machine_code)
    
    if activation_code:
        return jsonify({
            'success': True,
            'activation_code': activation_code
        })
    else:
        return jsonify({'error': '生成失败'}), 500

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # 0.0.0.0 允许外部访问
    app.run(host='0.0.0.0', port=5000, debug=False)
