from flask import Flask, request, jsonify
from paddleocr import PaddleOCR
import base64
import os
import tempfile
import re
import fitz  # PyMuPDF
import logging

# ================= 配置区域 =================
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
logging.getLogger('ppocr').setLevel(logging.WARNING)

app = Flask(__name__)

# ================= 模型加载 =================
print("-" * 30)
print("正在初始化 PaddleOCR 模型...")

try:
    ocr = PaddleOCR(lang='ch', use_angle_cls=True)
    print(">> 模型加载成功！")
except Exception as e:
    print(f">> 加载失败: {e}")
    try:
        ocr = PaddleOCR(lang='ch')
        print(">> 模型加载成功 (Basic Mode)")
    except Exception as e2:
        print(f">> 致命错误: {e2}")
        ocr = None

print("-" * 30)


@app.route('/health', methods=['GET'])
def health():
    if ocr:
        return jsonify({'status': 'ok', 'service': 'PaddleOCR Invoice API'})
    return jsonify({'status': 'error'}), 500


@app.route('/ocr/invoice', methods=['POST'])
def ocr_invoice():
    if not ocr:
        return jsonify({'error': 'Model not loaded', 'success': False}), 500

    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'error': 'No image provided', 'success': False}), 400
        
        try:
            img_data = base64.b64decode(data['image'])
        except:
            return jsonify({'error': 'Invalid Base64', 'success': False}), 400
        
        is_pdf = img_data[:4] == b'%PDF' or data.get('type') == 'pdf'
        suffix = '.pdf' if is_pdf else '.png'
        
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(img_data)
            temp_path = f.name
        
        img_path_to_ocr = temp_path

        try:
            if is_pdf:
                doc = fitz.open(temp_path)
                page = doc[0]
                mat = fitz.Matrix(2.0, 2.0) 
                pix = page.get_pixmap(matrix=mat)
                img_path_to_ocr = temp_path.replace('.pdf', '.png')
                pix.save(img_path_to_ocr)
                doc.close()
            
            # 【修复】新版PaddleOCR不支持cls参数，直接调用
            result = ocr.ocr(img_path_to_ocr)
            
            texts = []
            # 新版PaddleOCR可能返回None或空列表
            if result is not None:
                for page_result in result:
                    if page_result is not None:
                        for line in page_result:
                            if line and len(line) > 1 and line[1]:
                                # line[1] 可能是 (text, confidence) 或直接是 text
                                if isinstance(line[1], (tuple, list)):
                                    texts.append(str(line[1][0]))
                                else:
                                    texts.append(str(line[1]))
            
            print(f"识别成功，行数: {len(texts)}")
            
            if not texts:
                # 没有识别到文字，返回空结果
                return jsonify({
                    'success': True,
                    'amount': 0,
                    'date': '',
                    'number': '',
                    'code': '',
                    'buyer': '',
                    'seller': '',
                    'raw_text': [],
                    'message': 'No text detected'
                })
            
            full_text = '【' + '】【'.join(texts) + '】'
            invoice_data = parse_invoice_smart(full_text, texts)
            invoice_data['success'] = True
            
            return jsonify(invoice_data)
            
        finally:
            try:
                if os.path.exists(temp_path): os.unlink(temp_path)
                if is_pdf and os.path.exists(img_path_to_ocr): os.unlink(img_path_to_ocr)
            except: pass
                
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e), 'success': False}), 500


def parse_invoice_smart(full_text, raw_list):
    result = {
        'code': '', 'number': '', 'date': '', 'amount': 0,
        'buyer': '', 'seller': '', 'raw_text': raw_list
    }
    
    # 金额
    try:
        # 标准格式：小写、价税合计、¥
        amount_regex = re.compile(r'(?:小写|价税合计|¥|￥)\s*[:：]?\s*(\d+\.?\d*)')
        for txt in raw_list:
            match = amount_regex.search(txt)
            if match:
                result['amount'] = float(match.group(1))
                break
        # 火车票/机票格式：票价: ¥9.00
        if result['amount'] == 0:
            ticket_regex = re.compile(r'票价[：:]\s*[¥￥]?\s*(\d+\.?\d*)')
            for txt in raw_list:
                match = ticket_regex.search(txt)
                if match:
                    result['amount'] = float(match.group(1))
                    break
        # 财政票据格式：(小写) 6.80
        if result['amount'] == 0:
            fiscal_regex = re.compile(r'[（\(]小写[）\)]\s*(\d+\.?\d*)')
            for txt in raw_list:
                match = fiscal_regex.search(txt)
                if match:
                    result['amount'] = float(match.group(1))
                    break
        if result['amount'] == 0:
            all_nums = re.findall(r'(\d+\.\d{2})', full_text)
            valid = [float(x) for x in all_nums if 1 < float(x) < 100000000]
            if valid:
                result['amount'] = max(valid)
    except: pass

    # 发票号码
    try:
        m20 = re.search(r'(\d{20})', full_text)
        if m20:
            result['number'] = m20.group(1)
        else:
            m8 = re.findall(r'(?<!\d)(\d{8})(?!\d)', full_text)
            real = [c for c in m8 if not c.startswith('202')]
            if real: result['number'] = real[0]
            elif m8: result['number'] = m8[0]
    except: pass

    # 发票代码
    try:
        if len(result['number']) != 20:
            codes = re.findall(r'(?<!\d)(\d{10}|\d{12})(?!\d)', full_text)
            codes = [c for c in codes if c != result['number']]
            if codes: result['code'] = codes[0]
    except: pass

    # 日期
    try:
        date_match = re.search(r'(\d{4})\D+(\d{1,2})\D+(\d{1,2})', full_text)
        if date_match:
            y, m, d = date_match.groups()
            result['date'] = f"{y}-{int(m):02d}-{int(d):02d}"
    except: pass

    # 购买方
    try:
        # 标准格式
        m = re.search(r'购\s*买\s*方.*?名\s*称[：:]\s*([^\n\r【】]{5,50})', full_text)
        if m: 
            result['buyer'] = m.group(1).strip()
        else:
            # 财政票据：交款人
            m2 = re.search(r'交款人[：:]*\s*([^\n\r【】]{2,50})', full_text)
            if m2: result['buyer'] = m2.group(1).strip()
    except: pass

    # 销售方
    try:
        m = re.search(r'销\s*售\s*方.*?名\s*称[：:]\s*([^\n\r【】]{5,50})', full_text)
        if m: 
            result['seller'] = m.group(1).strip()
        else:
            # 财政票据：收款单位
            m2 = re.search(r'收款单位[：:]*\s*([^\n\r【】]{2,50})', full_text)
            if m2: result['seller'] = m2.group(1).strip()
    except: pass
    
    # 发票类型识别
    try:
        if '铁路' in full_text and '客票' in full_text:
            result['invoice_type'] = '铁路电子客票'
        elif '财政' in full_text and '票据' in full_text:
            result['invoice_type'] = '财政电子票据'
        elif '非税' in full_text:
            result['invoice_type'] = '财政电子票据'
        elif '专用发票' in full_text:
            result['invoice_type'] = '增值税专用发票'
        elif '普通发票' in full_text:
            result['invoice_type'] = '增值税普通发票'
        elif '电子发票' in full_text:
            result['invoice_type'] = '增值税电子普通发票'
    except: pass
    
    return result


if __name__ == '__main__':
    print("=" * 50)
    print("PaddleOCR Invoice API")
    print("端口: 8891")
    print("=" * 50)
    app.run(host='0.0.0.0', port=8891, debug=False)