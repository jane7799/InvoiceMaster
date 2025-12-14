
import os
import re
import cv2
import fitz
import tempfile
from PyQt6.QtGui import QImage, QPixmap
from src.utils.icons import Icons

try:
    from pyzbar.pyzbar import decode as decode_qr
    _PYZBAR_AVAILABLE = True
except ImportError:
    _PYZBAR_AVAILABLE = False

class InvoiceHelper:
    @staticmethod
    def thumb(fp):
        try: 
            with fitz.open(fp) as doc:
                return QPixmap.fromImage(QImage.fromData(doc.load_page(0).get_pixmap(matrix=fitz.Matrix(0.3,0.3)).tobytes("ppm")))
        except: return Icons.get("file", "#ccc").pixmap(100,100)
    
    @staticmethod
    def scan_invoice_qrcode(file_path):
        """扫描发票二维码获取结构化数据
        
        发票二维码格式：01,10,发票代码,发票号码,金额,日期,校验码,...
        返回解析后的字典，如果扫描失败返回None
        """
        if not _PYZBAR_AVAILABLE:
            return None
        
        try:
            # PDF需要先转换为图片
            with fitz.open(file_path) as doc:
                page = doc.load_page(0)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2倍放大提高识别率
                img_data = pix.tobytes("png")
                
                # 保存临时文件供cv2读取
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    tmp.write(img_data)
                    tmp_path = tmp.name
                
                try:
                    img = cv2.imread(tmp_path)
                    if img is None:
                        return None
                    
                    barcodes = decode_qr(img)
                    for barcode in barcodes:
                        data = barcode.data.decode("utf-8")
                        parts = data.split(',')
                        
                        if len(parts) >= 6:
                            # 标准格式：01,10,发票代码,发票号码,金额,日期,校验码
                            return {
                                "code": parts[2] if len(parts) > 2 else "",
                                "number": parts[3] if len(parts) > 3 else "",
                                "amount": float(parts[4]) if len(parts) > 4 and parts[4] else 0.0,
                                "date": parts[5] if len(parts) > 5 else "",
                                "check_code": parts[6] if len(parts) > 6 else "",
                            }
                finally:
                    os.unlink(tmp_path)
        except Exception as e:
            pass
        return None
    
    @staticmethod
    def parse_train_ticket(text):
        """专门解析铁路电子客票
        
        铁路电子客票格式特点：
        - 发票号码：20位
        - 金额格式：票价: ¥9.00
        - 特有字段：出发站、到达站、车次、座位类型、乘客姓名
        
        返回与OCR接口一致的字典格式。
        """
        result = {
            "date": "",
            "amount": 0.0,
            "seller": "",
            "seller_tax_id": "",
            "buyer": "",
            "buyer_tax_id": "",
            "code": "",
            "number": "",
            "check_code": "",
            "invoice_type": "铁路电子客票",
            "item_name": "",
            "remark": "",
            # 火车票特有字段
            "departure_station": "",  # 出发站
            "arrival_station": "",    # 到达站
            "train_number": "",       # 车次
            "seat_type": "",          # 座位类型
            "passenger_name": "",     # 乘客姓名
        }
        
        try:
            # 1. 提取发票号码（20位，如24329130548000000001）
            m_num = re.search(r'发票号[码]?[：:]*\s*(\d{20})', text)
            if m_num:
                result["number"] = m_num.group(1)
            else:
                # 回退：直接提取20位数字
                nums = re.findall(r'(?<!\d)(\d{20})(?!\d)', text)
                if nums:
                    result["number"] = nums[0]
            
            # 2. 提取日期（开票日期或乘车日期）
            m_date = re.search(r'(?:开票日期|乘车日期)[：:]*\s*(\d{4})[-年](\d{1,2})[-月](\d{1,2})', text)
            if m_date:
                result["date"] = f"{m_date.group(1)}-{m_date.group(2).zfill(2)}-{m_date.group(3).zfill(2)}"
            else:
                m_date2 = re.search(r'(\d{4})[-年](\d{1,2})[-月](\d{1,2})', text)
                if m_date2:
                    result["date"] = f"{m_date2.group(1)}-{m_date2.group(2).zfill(2)}-{m_date2.group(3).zfill(2)}"
            
            # 3. 提取金额（票价: ¥9.00 格式）
            m_amount = re.search(r'票价[：:]*\s*[¥￥]?\s*([0-9,.]+)', text)
            if m_amount:
                result["amount"] = float(m_amount.group(1).replace(",", ""))
            else:
                # 回退：价税合计格式
                m_amount2 = re.search(r'价税合计[^¥￥\d]*[¥￥]?\s*([0-9,.]+)', text)
                if m_amount2:
                    result["amount"] = float(m_amount2.group(1).replace(",", ""))
                else:
                    # 再回退：直接匹配 ¥ 后的金额
                    amounts = re.findall(r'[¥￥]\s*([0-9,.]+)', text)
                    if amounts:
                        result["amount"] = max([float(x.replace(",", "")) for x in amounts])
            
            # 4. 提取出发站和到达站
            m_stations = re.search(r'([^\n\r]{2,10}[站])\s*[→\-—至到]\s*([^\n\r]{2,10}[站])', text)
            if m_stations:
                result["departure_station"] = m_stations.group(1).strip()
                result["arrival_station"] = m_stations.group(2).strip()
            else:
                # 分别匹配
                stations = re.findall(r'([^\n\r\s]{2,8}站)', text)
                if len(stations) >= 2:
                    result["departure_station"] = stations[0]
                    result["arrival_station"] = stations[1]
            
            # 5. 提取车次（如K850、G123、D456）
            m_train = re.search(r'([GCDKTZ]\d{1,4})', text)
            if m_train:
                result["train_number"] = m_train.group(1)
            
            # 6. 提取座位类型（硬座、软座、硬卧、软卧、二等座、一等座等）
            seat_types = re.findall(r'(硬座|软座|硬卧|软卧|二等座|一等座|商务座|特等座|无座|新空调\s*\S+)', text)
            if seat_types:
                result["seat_type"] = seat_types[0].replace("\n", "").strip()
            
            # 7. 提取乘客姓名（格式：3425011989****5014\n谭彬）
            # 先匹配带*的身份证号后面的姓名
            m_passenger = re.search(r'\d{10}\*{4}\d{4}\n([^\n\r\d]{2,4})', text)
            if m_passenger:
                result["passenger_name"] = m_passenger.group(1).strip()
                if not result["buyer"]:
                    result["buyer"] = m_passenger.group(1).strip()
            
            # 8. 提取购买方名称（单位名称）
            # 方法1：购买方名称: 格式
            m_buyer = re.search(r'购买方名称[：:]\s*([^\n\r]{2,50})', text)
            if m_buyer and m_buyer.group(1).strip():
                result["buyer"] = m_buyer.group(1).strip()
            else:
                # 方法2：统一社会信用代码前一行的单位名称
                m_unit = re.search(r'([^\n\r]{5,50}(?:公司|单位|中心|联络处|处|局|厅|院|所|站|部))\n统一社会信用代码', text)
                if m_unit:
                    result["buyer"] = m_unit.group(1).strip()
                else:
                    # 方法3：匹配政府机关/企业名称格式
                    units = re.findall(r'([^\n\r]{5,50}(?:公司|单位|中心|联络处|处|局|厅|院|所|站|部|协会))', text)
                    # 过滤掉销售方相关的（国家铁路、12306等）
                    buyer_units = [u for u in units if '铁路' not in u and '12306' not in u and '祝您' not in u]
                    if buyer_units:
                        result["buyer"] = buyer_units[0].strip()
            
            # 9. 提取购买方税号（单位的统一社会信用代码）
            m_tax = re.search(r'统一社会信用代码[：:]*\s*([A-Za-z0-9]{15,20})', text)
            if m_tax:
                result["buyer_tax_id"] = m_tax.group(1)
            
            # 9. 提取电子客票号
            m_ticket = re.search(r'电子客票号[：:]*\s*(\d{18,24})', text)
            if m_ticket:
                result["check_code"] = m_ticket.group(1)
            
            # 10. 设置项目名称
            if result["departure_station"] and result["arrival_station"]:
                result["item_name"] = f"{result['departure_station']}-{result['arrival_station']}"
                if result["train_number"]:
                    result["item_name"] += f" {result['train_number']}"
            elif result["train_number"]:
                result["item_name"] = f"铁路客票 {result['train_number']}"
            else:
                result["item_name"] = "铁路电子客票"
            
            # 11. 备注：座位类型和乘客姓名
            remarks = []
            if result["seat_type"]:
                remarks.append(result["seat_type"])
            if result["passenger_name"]:
                remarks.append(f"乘客:{result['passenger_name']}")
            result["remark"] = " ".join(remarks)
            
            # 12. 设置销售方为中国国家铁路集团（火车票统一销售方）
            result["seller"] = "中国国家铁路集团有限公司"
            result["seller_tax_id"] = ""  # 火车票不需要销售方税号
        
        except Exception as e:
            pass
        
        return result
    
    @staticmethod
    def parse_fiscal_receipt(text):
        """专门解析财政票据（非税收入票据）
        
        财政票据格式与普通发票不同：
        - 票据代码（8位）
        - 票据号码（10位）
        - 交款人（购买方）
        - 收款单位（销售方）
        - 金额格式特殊
        
        返回与OCR接口一致的字典格式。
        """
        result = {
            "date": "",
            "amount": 0.0,
            "seller": "",
            "seller_tax_id": "",
            "buyer": "",
            "buyer_tax_id": "",
            "code": "",
            "number": "",
            "check_code": "",
            "invoice_type": "财政电子票据",
            "item_name": "",
            "remark": "",
        }
        
        try:
            # 1. 提取日期
            m_date = re.search(r'(\d{4})[-年](\d{1,2})[-月](\d{1,2})', text)
            if m_date:
                result["date"] = f"{m_date.group(1)}-{m_date.group(2).zfill(2)}-{m_date.group(3).zfill(2)}"
            
            # 2. 提取金额
            # 方法1：匹配 (小写) 6.80 格式
            m_amount = re.search(r'[（\(]小写[）\)]\s*([0-9,.]+)', text)
            if m_amount:
                result["amount"] = float(m_amount.group(1).replace(",", ""))
            else:
                # 方法2：直接提取独立的小数金额
                all_amounts = re.findall(r'(?<!\d)(\d{1,6}\.\d{2})(?!\d)', text)
                if all_amounts:
                    # 过滤掉可能的税率
                    valid_amounts = [float(x) for x in all_amounts if 0.5 < float(x) < 100000]
                    if valid_amounts:
                        result["amount"] = valid_amounts[0]
            
            # 3. 提取票据代码（8位，如11010125）
            m_code = re.search(r'票据代码[：:]*\s*(\d{8})', text)
            if m_code:
                result["code"] = m_code.group(1)
            else:
                # 回退：提取第一个8位数字（排除日期）
                codes = re.findall(r'(?<!\d)(\d{8})(?!\d)', text)
                codes = [c for c in codes if not c.startswith('202')]
                if codes:
                    result["code"] = codes[0]
            
            # 4. 提取票据号码（10位，如0078698312）
            m_num = re.search(r'票据号码[：:]*\s*(\d{10})', text)
            if m_num:
                result["number"] = m_num.group(1)
            else:
                # 回退：提取10位数字
                nums = re.findall(r'(?<!\d)(\d{10})(?!\d)', text)
                nums = [n for n in nums if n != result.get("code")]
                if nums:
                    result["number"] = nums[0]
            
            # 5. 提取校验码（6位）
            m_check = re.search(r'校验码[：:]*\s*(\d{6}|\w{6})', text)
            if m_check:
                result["check_code"] = m_check.group(1)
            else:
                # 回退：提取6位十六进制或数字
                checks = re.findall(r'(?<!\d)(\d{6}|[0-9a-fA-F]{6})(?!\d)', text)
                # 排除已识别的号码
                for c in checks:
                    if c != result.get("code") and c not in (result.get("number") or ""):
                        result["check_code"] = c
                        break
            
            # 6. 提取交款人（购买方）和收款单位（销售方）
            # 交款人：财政票据通常格式 "交款人: XXXX  统一社会信用代码: YYYY"
            # 原来的正则太过贪婪，容易把后面的“统一社会...”也吃进来
            m_payer = re.search(r'交款人[：:]*\s*([^\n\r]{2,60})', text)
            if m_payer:
                raw_buyer = m_payer.group(1).strip()
                # 如果包含统一社会信用代码，截断之
                if "统一社会信用" in raw_buyer:
                    raw_buyer = raw_buyer.split("统一社会信用")[0].strip()
                result["buyer"] = raw_buyer
            
            # 收款单位
            m_payee = re.search(r'收款单位[（(章）)]*[：:]*\s*([^\n\r]{2,60})', text)
            if m_payee:
                raw_seller = m_payee.group(1).strip()
                # 同样防止贪婪匹配，把后面的“交款人”或“复核”等字样吃进来
                for stop_word in ["交款人", "复核", "统一社会信用"]:
                    if stop_word in raw_seller:
                        raw_seller = raw_seller.split(stop_word)[0].strip()
                result["seller"] = raw_seller
            
            # 如果没有找到，从公司名称中识别
            if not result["buyer"] or not result["seller"]:
                company_pattern = r'([^\n\r]{3,50}(?:公司|单位|中心|联络处|处|局|厅|院|所|站|部|协会|基金|集团|代收))'
                companies = re.findall(company_pattern, text)
                seen = set()
                unique_companies = []
                for c in companies:
                    c = c.strip()
                    if c and c not in seen and len(c) > 3:
                        seen.add(c)
                        unique_companies.append(c)
                
                for c in unique_companies:
                    if not result["seller"] and ('代收' in c or '集团' in c or '供水' in c or '自来水' in c):
                        result["seller"] = c
                    elif not result["buyer"] and ('联络处' in c or '政府' in c or '机关' in c):
                        result["buyer"] = c
                
                # 如果还没识别出来，按反向顺序（财政票据收款方在前）
                if not result["buyer"] and not result["seller"] and len(unique_companies) >= 2:
                    result["seller"] = unique_companies[0]
                    result["buyer"] = unique_companies[1]
            
            # 7. 提取交款人税号
            m_tax = re.search(r'统一社会信用代码[：:]*\s*([A-Za-z0-9]{15,20})', text)
            if m_tax:
                result["buyer_tax_id"] = m_tax.group(1)
            else:
                # 回退：提取Y开头的统一社会信用代码
                tax_ids = re.findall(r'(Y?\d{17,18}[A-Za-z0-9]?)', text)
                if tax_ids:
                    result["buyer_tax_id"] = tax_ids[0]
            
            # 8. 提取项目名称
            m_item = re.search(r'(?:项目名称|费用名称)[：:]*\s*([^\n\r]{2,30})', text)
            if m_item:
                result["item_name"] = m_item.group(1).strip()
            else:
                # 回退：匹配费（居民）等格式
                m_item2 = re.search(r'([^\n\r]{2,20}费[（(][^\n\r)）]{1,10}[）)])', text)
                if m_item2:
                    result["item_name"] = m_item2.group(1)
            
        except Exception as e:
            pass
        
        return result
    
    @staticmethod
    def parse_list(text):
        """专门解析【销售货物或者提供应税劳务、服务清单】
        
        清单特点：
        - 标题包含“清单”
        - 包含“所属增值税专用发票代码”、“号码”
        - 有购买方、销售方信息
        - 有小计金额
        """
        result = {
            "date": "",
            "amount": 0.0,
            "seller": "",
            "seller_tax_id": "",
            "buyer": "",
            "buyer_tax_id": "",
            "code": "",
            "number": "",
            "check_code": "",
            "invoice_type": "发票清单",
            "item_name": "（详见清单明细）",
            "remark": "发票清单",
        }
        
        try:
            # 1. 提取所属发票号码/代码
            # 格式：所属增值税专用发票代码: 123... 号码: 456...
            m_code = re.search(r'代码[：:]\s*(\d{10,12})', text)
            if m_code: result["code"] = m_code.group(1)
            
            m_num = re.search(r'号码[：:]\s*(\d{8,20})', text)
            if m_num: result["number"] = m_num.group(1)
            
            # 2. 提取金额（小计/总计）
            # 格式：小计 ¥123.00 或 总计
            m_amt = re.search(r'(?:小计|合计|总计)[^0-9]*[¥￥]?\s*([0-9,.]+)', text)
            if m_amt:
                try:
                    val = float(m_amt.group(1).replace(",", ""))
                    result["amount"] = val
                except: pass
            
            # 3. 提取销售方/购买方 (通常在底部或顶部)
            # 销售方名称：xxx
            m_seller = re.search(r'销售方名称[：:]\s*([^\n\s]+)', text)
            if m_seller: result["seller"] = m_seller.group(1)
            
            m_buyer = re.search(r'购买方名称[：:]\s*([^\n\s]+)', text)
            if m_buyer: result["buyer"] = m_buyer.group(1)
            
            # 4. 尝试提取日期 (填开日期)
            m_date = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', text)
            if m_date:
                dt = m_date.group(1)
                result["date"] = dt.replace("年", "-").replace("月", "-").replace("日", "")
            
        except Exception: pass
        
        return result

    @staticmethod
    def parse_invoice_local(file_path):
        """本地解析发票完整信息（适用于矢量PDF）
        
        优先使用二维码扫描获取核心数据，然后用文字提取补充其他字段。
        返回与OCR接口一致的字典格式。
        """
        result = {
            "date": "",
            "amount": 0.0,
            "amount_without_tax": "",
            "tax_amt": "",
            "tax_rate": "",
            "seller": "",
            "seller_tax_id": "",
            "buyer": "",
            "buyer_tax_id": "",
            "code": "",
            "number": "",
            "check_code": "",
            "invoice_type": "",
            "item_name": "",
            "remark": "",
            "machine_code": "",
            "_local_parsed": True,
        }
        
        # 首先尝试二维码扫描（最准确）
        qr_data = InvoiceHelper.scan_invoice_qrcode(file_path)
        if qr_data:
            result["code"] = qr_data.get("code", "")
            result["number"] = qr_data.get("number", "")
            result["amount"] = qr_data.get("amount", 0.0)
            result["check_code"] = qr_data.get("check_code", "")
            # 日期格式转换：二维码中可能是 YYYYMMDD
            qr_date = qr_data.get("date", "")
            if qr_date and len(qr_date) == 8:
                result["date"] = f"{qr_date[:4]}-{qr_date[4:6]}-{qr_date[6:8]}"
            elif qr_date:
                result["date"] = qr_date
        
        try:
            with fitz.open(file_path) as doc:
                # 使用x坐标（水平位置）区分购买方（左边）和销售方（右边）
                # 同时使用红色标签作为辅助判断
                
                buyer_name = ""
                buyer_tax = ""
                seller_name = ""
                seller_tax = ""
                all_text_parts = []
                
                for page in doc:
                    page_width = page.rect.width
                    mid_x = page_width / 2  # 页面中点，用于区分左右
                    
                    blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)["blocks"]
                    
                    for block in blocks:
                        if "lines" not in block:
                            continue
                        
                        # block 有 bbox，可以判断整个block的位置
                        block_x = block.get("bbox", [0, 0, 0, 0])[0]
                        
                        for line in block["lines"]:
                            line_bbox = line.get("bbox", [0, 0, 0, 0])
                            
                            line_black = ""
                            
                            for span in line["spans"]:
                                text = span["text"]
                                span_bbox = span.get("bbox", [0, 0, 0, 0])
                                span_x = span_bbox[0]
                                color = span.get("color", 0)
                                r = (color >> 16) & 0xFF
                                g = (color >> 8) & 0xFF
                                b = color & 0xFF
                                
                                is_red = (r > 150 and g < 100 and b < 100)
                                is_dark = (r < 100 and g < 100 and b < 100)
                                
                                if is_red:
                                    pass # 标签
                                elif is_dark:
                                    line_black += text
                                    
                                    # 直接根据x坐标判断归属
                                    # 左边（x < mid_x）是购买方，右边是销售方
                                    is_left = span_x < mid_x
                                    
                                    # 提取公司名
                                    m_company = re.search(r'([^\n\r]{3,50}(?:公司|单位|中心|联络处|处|局|厅|院|所|站|部|协会|基金|集团))', text)
                                    if m_company:
                                        if is_left and not buyer_name:
                                            buyer_name = m_company.group(1).strip()
                                        elif not is_left and not seller_name:
                                            seller_name = m_company.group(1).strip()
                                    
                                    # 提取税号（统一社会信用代码）
                                    # 税号特征：18位字母数字组合，通常以字母或数字开头
                                    # 发票号码：8位或20位纯数字（需排除）
                                    m_tax = re.search(r'([A-Za-z0-9]{15,18})', text)
                                    if m_tax:
                                        tax_id = m_tax.group(1)
                                        # 排除8位和20位纯数字（发票号码）
                                        is_invoice_number = (len(tax_id) in [8, 20]) and tax_id.isdigit()
                                        # 税号应该包含字母或者是15-18位数字
                                        is_valid_tax = len(tax_id) >= 15 and len(tax_id) <= 18
                                        if is_valid_tax and not is_invoice_number:
                                            if is_left and not buyer_tax:
                                                buyer_tax = tax_id
                                            elif not is_left and not seller_tax:
                                                seller_tax = tax_id
                            
                            if line_black.strip():
                                all_text_parts.append(line_black)
                
                # 存储提取的购买方/销售方信息
                if buyer_name:
                    result["buyer"] = buyer_name
                if buyer_tax:
                    result["buyer_tax_id"] = buyer_tax
                if seller_name:
                    result["seller"] = seller_name
                if seller_tax:
                    result["seller_tax_id"] = seller_tax
                
                text = "\n".join(all_text_parts)
                
                # 如果没有提取到文字，回退到全部文字
                if not text.strip():
                    text = "\n".join([page.get_text() for page in doc])
                
                # 获取完整文本用于特殊票据检测
                full_raw_text = "\n".join([page.get_text() for page in doc])
                
                # [V3.5 新增] 检测“清单”逻辑
                # 必须同时包含“清单”和“所属”（例如：所属增值税专用发票代码）
                # 普通发票虽然也有“销售货物...清单”字样（列名），但绝对不会有“所属”这个词
                if "清单" in full_raw_text and "所属" in full_raw_text:
                     # 这是一个清单文件
                     list_result = InvoiceHelper.parse_list(full_raw_text)
                     # 如果解析出有效信息（至少有金额或号码），直接返回
                     if list_result.get("amount", 0) > 0 or list_result.get("number"):
                         return list_result
                
                # [V3.5 新增] 检测“入住凭证”等非发票文档（如携程入住凭证）
                # 用户不希望这些单纯的消费凭证混入发票台账
                # 扩展检测：行程报销单、结算单、普通入住凭证
                is_non_invoice = False
                non_invoice_type = "非发票凭证"
                non_invoice_name = "非发票凭证"
                
                if "入住凭证" in full_raw_text:
                    is_non_invoice = True
                    non_invoice_name = "入住凭证（非发票）"
                elif "行程报销单" in full_raw_text:
                    is_non_invoice = True
                    non_invoice_name = "行程报销单（非发票）"
                elif "结算单" in full_raw_text and "发票" not in full_raw_text:
                    # 结算单必须要小心，防止误伤带“结算单”字样的发票
                    is_non_invoice = True
                    non_invoice_name = "结算单（非发票）"
                    
                if is_non_invoice:
                    return {
                        "date": "", "amount": 0.0, "number": "", "code": "",
                        "invoice_type": non_invoice_type, 
                        "item_name": non_invoice_name,
                        "check_code": "", "buyer": "", "seller": ""
                    }
                
                # 兼容性处理：如果 private_ocr_url 未配置，则不进行本地坐标解析（防止干扰）
                
                # [V3.5 修复] 优化识别条件：必须包含“铁路”且“客票”，或者是明确的“火车票”标识
                # 之前的 '列车' 太泛，容易误伤包含该词的普通发票（丢失税号）
                is_train_ticket = ('铁路' in full_raw_text and '客票' in full_raw_text) or '中国铁路' in full_raw_text
                
                if is_train_ticket:
                    train_result = InvoiceHelper.parse_train_ticket(full_raw_text)
                    if train_result and train_result['amount'] > 0:
                        # ⚠️ 修正逻辑：火车票解析器更准确，应该覆盖通用解析的结果
                        # 通用解析可能因排版问题把“购买方税号”误判为“销售方税号”，需要被 train_result 纠正
                        
                        for k, v in train_result.items():
                            if v:
                                result[k] = v
                        
                        # 特别强制覆盖销售方信息 (火车票固定且无税号)
                        # 即使 result 中已经有了（可能是误判的），也要强制被 train_result (空值) 覆盖
                        result["seller"] = train_result["seller"]
                        result["seller_tax_id"] = train_result["seller_tax_id"]
                            
                        # 如果没有二维码，尝试从火车票解析结果中获取基本信息
                        if not result.get("code") and train_result.get("code"): result["code"] = train_result["code"]
                        if not result.get("number") and train_result.get("number"): result["number"] = train_result["number"]
                        if not result.get("date") and train_result.get("date"): result["date"] = train_result["date"]
                        
                        return result
                
                # 检测财政电子票据
                if '财政' in full_raw_text or '非税' in full_raw_text:
                    fiscal_result = InvoiceHelper.parse_fiscal_receipt(full_raw_text)
                    if fiscal_result and fiscal_result.get('amount', 0) > 0:
                        # [修复] 财政票据解析器的结果应该优先覆盖通用解析
                        # 之前的逻辑只在 result 没有值时才赋值，导致错误的二维码解析结果无法被覆盖
                        for k, v in fiscal_result.items():
                            if v:  # 只要财政解析器有值，就覆盖
                                result[k] = v
                        return result

                # 普通发票解析逻辑（继续）
                if not result.get("date"):
                    m_date = re.search(r'(\d{4})[-年](\d{1,2})[-月](\d{1,2})', text)
                    if m_date:
                        result["date"] = f"{m_date.group(1)}-{m_date.group(2).zfill(2)}-{m_date.group(3).zfill(2)}"
                
                if not result.get("code"):
                    m_code = re.search(r'(?<!\d)(\d{10,12})(?!\d)', text)
                    if m_code: result["code"] = m_code.group(1)
                    
                if not result.get("number"):
                    m_num = re.search(r'(?<!\d)(\d{8}|0\d{8})(?!\d)', text) # 特例：有些号码前面带0
                    if m_num: result["number"] = m_num.group(1)
                    
                if not result.get("amount") or result.get("amount") == 0:
                    # 尝试匹配 小写：123.00
                    amounts = re.findall(r'[¥￥]\s*([0-9,.]+)', text)
                    if amounts:
                        # 通常金额是最大的那个（可能是价税合计）
                        valid_amounts = []
                        for x in amounts:
                            try:
                                val = float(x.replace(",", ""))
                                # [V3.5 修复] 排除极大的数值（防止误匹配到发票代码，如 25427000000）
                                # 发票代码通常是 10/12/20 位数字，且如果是金额则会非常巨大
                                if val > 100000000 and float(x.replace(",", "").replace(".", "")) == val: 
                                    continue # 排除像是纯数字的长串
                                    
                                # 排除与发票代码/号码相同的数值
                                if str(int(val)) == result.get("code") or str(int(val)) == result.get("number"):
                                    continue
                                    
                                valid_amounts.append(val)
                            except: pass
                        if valid_amounts:
                            result["amount"] = max(valid_amounts)
                
                # 尝试提取发票类型
                if "增值税专用发票" in full_raw_text:
                    result["invoice_type"] = "增值税专用发票"
                elif "增值税普通发票" in full_raw_text:
                    result["invoice_type"] = "增值税普通发票"
                elif "电子发票" in full_raw_text:
                    result["invoice_type"] = "电子发票"
                    
                # [V3.5] 尝试提取项目名称 (针对电子发票)
                # 寻找 “货物或应税劳务、服务名称” 下方的第一行内容
                # 这是一个启发式规则，尝试捕获 *运输服务*xxx 或 *餐饮服务*xxx 等常见格式
                if not result.get("item_name"):
                    # 匹配常见的发票商品名格式：*分类*商品名
                    # 例如：*运输服务*客运服务费
                    m_item = re.search(r'(\*[\u4e00-\u9fa5]+\*[^\n\s]+)', text)
                    if m_item:
                        result["item_name"] = m_item.group(1).strip()
                    else:
                        # 回退：寻找 “货物或应税劳务、服务名称” 后的下一段文字
                        # 有些清单不带星号分类，例如直接写“办公用品”
                        try:
                            # 简单的基于行号的尝试，找到标题后的非空行
                            lines = text.split('\n')
                            for i, line in enumerate(lines):
                                if "货物或应税劳务" in line or "服务名称" in line:
                                    # 往下找最多3行，忽略空行和无关行
                                    for j in range(1, 4):
                                        if i + j < len(lines):
                                            candidate = lines[i+j].strip()
                                            # 排除规格型号、单位、数量等列名（虽然通常横向排一排，但在text里可能换行）
                                            if candidate and "规格" not in candidate and "单位" not in candidate and "金额" not in candidate:
                                                # 简单的过滤：长度大于1，不全是数字
                                                if len(candidate) > 1 and not candidate.replace('.','').isdigit():
                                                    result["item_name"] = candidate
                                                    break
                                    break
                        except: pass
                
        except Exception as e:
            pass
            
        return result

    @staticmethod
    def _is_result_complete(result):
        """检查解析结果是否完整（足以跳过OCR）"""
        if not result:
            return False
            
        # 必须要有核心金额
        if not result.get("amount") or float(result.get("amount", 0)) <= 0:
            return False
            
        # 必须要有日期
        if not result.get("date"):
            return False
            
        # 必须要有发票号码（或票据代码）
        if not result.get("number") and not result.get("code"):
            return False

        # [V3.5] 必须要有商品名称/项目名称 (否则认为不完整，需要OCR补充细节)
        # 火车票/财政票据本地解析能拿到这个字段，普通发票拿不到则会去走OCR
        if not result.get("item_name"):
            return False
            
        return True
