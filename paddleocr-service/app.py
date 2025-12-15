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
    
    # 金额（优先获取价税合计/含税金额）
    # [V3.6 修复] 增强金额识别，处理OCR将"价税合计"和金额分成不同行的情况
    try:
        # === 第一阶段：在完整文本中搜索（处理分行情况）===
        # 将所有文本合并，用空格分隔（模拟连续文本）
        merged_text = ' '.join(raw_list)
        
        # 第一优先级：明确的"价税合计"或"小写"后的金额（这是含税总金额）
        # 增加更宽松的匹配模式，处理OCR分行情况
        total_patterns = [
            r'(?:价税合计|价税\s*合\s*计)[^0-9¥￥]*[¥￥]?\s*[:：]?\s*(\d+[,，]?\d*\.?\d*)',  # 价税合计格式
            r'[（\(]小写[）\)]\s*[¥￥]\s*(\d+[,，]?\d*\.\d{2})',  # (小写) ¥22.50 格式（精确匹配）
            r'小写[）\)]\s*[¥￥]\s*(\d+[,，]?\d*\.\d{2})',  # 小写) ¥22.50 格式
            r'[（\(]\s*小写\s*[）\)]\s*[¥￥]\s*(\d+[,，]?\d*\.?\d*)',  # ( 小写 ) ¥22.50 格式
            r'小写[^0-9¥￥]*[¥￥]\s*(\d+[,，]?\d*\.\d{2})',  # 小写...¥22.50 宽松格式
            r'税\s*合\s*计[^0-9¥￥]*[¥￥]?\s*(\d+[,，]?\d*\.?\d*)',  # 仅"税合计"
        ]
        
        for pattern in total_patterns:
            total_regex = re.compile(pattern)
            # 先在合并文本中搜索
            match = total_regex.search(merged_text)
            if match:
                amount_str = match.group(1).replace(',', '').replace('，', '')
                result['amount'] = float(amount_str)
                break
            # 再逐行搜索
            if result['amount'] == 0:
                for txt in raw_list:
                    match = total_regex.search(txt)
                    if match:
                        amount_str = match.group(1).replace(',', '').replace('，', '')
                        result['amount'] = float(amount_str)
                        break
                if result['amount'] > 0:
                    break
        
        # === 第二阶段：处理相邻行的情况 ===
        # OCR 有时会将 "价税合计" 和 "¥100.00" 识别为相邻的两行
        if result['amount'] == 0:
            for i, txt in enumerate(raw_list):
                if '价税合计' in txt or '小写' in txt or '税合计' in txt:
                    # 在当前行和下几行中查找金额
                    for j in range(0, min(3, len(raw_list) - i)):
                        amount_match = re.search(r'[¥￥]?\s*(\d+[,，]?\d*\.\d{2})', raw_list[i + j])
                        if amount_match:
                            amount_str = amount_match.group(1).replace(',', '').replace('，', '')
                            result['amount'] = float(amount_str)
                            break
                    if result['amount'] > 0:
                        break
        
        # 第三优先级：处理"合计金额 ¥100（含税/未含税）"格式
        if result['amount'] == 0:
            # 检查是否有"含税"和"未含税"标记
            has_tax_inclusive = '含税' in full_text and '未含税' not in full_text
            has_tax_exclusive = '未含税' in full_text or '不含税' in full_text
            
            combined_regex = re.compile(r'合计金额\s*[¥￥]?\s*(\d+[,，]?\d*\.?\d*)')
            for txt in raw_list:
                match = combined_regex.search(txt)
                if match:
                    amount_str = match.group(1).replace(',', '').replace('，', '')
                    amount_val = float(amount_str)
                    if has_tax_exclusive:
                        # 这是未含税金额，存到额外字段，后续可能需要加税
                        result['amount_without_tax'] = str(amount_val)
                        # 仍然设置为主金额（如果没有其他来源）
                        result['amount'] = amount_val
                    else:
                        result['amount'] = amount_val
                    break
        
        # 第四优先级：标准 ¥ 符号后的金额（但要排除不含税金额）
        if result['amount'] == 0:
            # 收集所有 ¥ 后的金额
            all_yen_amounts = []
            standard_regex = re.compile(r'[¥￥]\s*[:：]?\s*(\d+[,，]?\d*\.?\d*)')
            for txt in raw_list:
                for match in standard_regex.finditer(txt):
                    try:
                        amount_str = match.group(1).replace(',', '').replace('，', '')
                        val = float(amount_str)
                        if val > 0.5:  # 排除太小的值
                            all_yen_amounts.append(val)
                    except: pass
            
            # 通常价税合计是最大的金额
            if all_yen_amounts:
                result['amount'] = max(all_yen_amounts)
        
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
        
        # 最后回退：取所有金额中的最大值（通常价税合计最大）
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