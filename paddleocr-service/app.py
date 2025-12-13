from flask import Flask, request, jsonify
from paddleocr import PaddleOCR
import base64
import os
import tempfile
import re
import fitz  # PyMuPDF for PDF support

app = Flask(__name__)

# 初始化PaddleOCR（中文模型）
print("正在加载PaddleOCR模型...")
ocr = PaddleOCR(lang='ch')
print("PaddleOCR模型加载完成！")


@app.route('/health', methods=['GET'])
def health():
    """健康检查接口"""
    return jsonify({'status': 'ok', 'service': 'PaddleOCR Invoice API'})


@app.route('/ocr/invoice', methods=['POST'])
def ocr_invoice():
    """发票OCR识别接口
    
    请求体(JSON):
        - image: Base64编码的图片或PDF数据
        - type: 可选，'image' 或 'pdf'，默认自动检测
    
    返回:
        - code: 发票代码
        - number: 发票号码
        - date: 开票日期
        - amount: 价税合计金额
        - raw_text: 原始识别文本列表
    """
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'error': 'No image provided', 'code': 400}), 400
        
        # Base64解码
        img_data = base64.b64decode(data['image'])
        
        # 检测是否为PDF
        is_pdf = img_data[:4] == b'%PDF' or data.get('type') == 'pdf'
        
        # 保存临时文件
        suffix = '.pdf' if is_pdf else '.png'
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(img_data)
            temp_path = f.name
        
        try:
            # 如果是PDF，先转换为图片
            if is_pdf:
                doc = fitz.open(temp_path)
                page = doc[0]
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                img_path = temp_path.replace('.pdf', '.png')
                pix.save(img_path)
                doc.close()
                os.unlink(temp_path)
                temp_path = img_path
            
            # OCR识别
            result = ocr.ocr(temp_path)
            
            # 提取文字
            texts = []
            if result and result[0]:
                for line in result[0]:
                    if line[1]:
                        texts.append(line[1][0])
            
            full_text = '【' + '】【'.join(texts) + '】'
            
            # 解析发票信息
            invoice_data = parse_invoice(full_text, texts)
            invoice_data['success'] = True
            
            return jsonify(invoice_data)
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


def parse_invoice(text, raw_texts):
    """解析发票信息"""
    result = {'raw_text': raw_texts}
    
    # 发票号码 (8位数字，全电发票可能是20位)
    try:
        # 先尝试20位（全电发票）
        nums = re.findall(r'【(\d{20})】', text)
        if nums:
            result['number'] = nums[0]
            result['code'] = ''  # 全电发票无发票代码
        else:
            # 传统发票8位号码
            result['number'] = re.findall(r'【(\d{8})】', text)[0]
    except:
        result['number'] = ''
    
    # 发票代码 (10-12位数字)
    clean_text = re.sub('[a-zA-Z]', '', text)
    try:
        codes = re.findall(r'【(\d{10,12})】', clean_text)
        result['code'] = codes[0] if codes else ''
    except:
        result['code'] = ''
    
    # 金额 (提取所有金额，取合适的值)
    try:
        amounts = re.findall(r'¥?(\d+\.\d{2})', text)
        amounts = [float(a) for a in amounts]
        amounts = list(set(amounts))  # 去重
        amounts.sort(reverse=True)
        # 取最大的金额（通常是价税合计）
        result['amount'] = amounts[0] if amounts else 0
    except:
        result['amount'] = 0
    
    # 日期
    try:
        # 匹配多种日期格式
        patterns = [
            r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})',
            r'(\d{4})(\d{2})(\d{2})日'
        ]
        for pattern in patterns:
            date_match = re.findall(pattern, text)
            if date_match:
                y, m, d = date_match[0]
                result['date'] = f'{y}-{str(m).zfill(2)}-{str(d).zfill(2)}'
                break
        else:
            result['date'] = ''
    except:
        result['date'] = ''
    
    # 尝试提取购买方/销售方名称
    try:
        # 查找"名称："后的内容
        names = re.findall(r'名称[：:]\s*([^\【\】]+)', text)
        if len(names) >= 2:
            result['buyer'] = names[0].strip()
            result['seller'] = names[1].strip()
        else:
            result['buyer'] = ''
            result['seller'] = ''
    except:
        result['buyer'] = ''
        result['seller'] = ''
    
    return result


if __name__ == '__main__':
    print("=" * 50)
    print("PaddleOCR Invoice API Service")
    print("端口: 8891")
    print("健康检查: GET /health")
    print("发票识别: POST /ocr/invoice")
    print("=" * 50)
    app.run(host='0.0.0.0', port=8891, debug=False)
