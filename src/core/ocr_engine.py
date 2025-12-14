"""
OCR 引擎模块
提供发票 OCR 识别和本地解析功能
"""
import os
import re
import base64
import time
import logging
import requests
import fitz  # PyMuPDF

from PyQt6.QtCore import QSettings, QByteArray
from PyQt6.QtGui import QPixmap, QImage, QIcon


class InvoiceHelper:
    """发票处理助手类"""
    
    @staticmethod
    def thumb(fp):
        """生成发票缩略图"""
        try:
            with fitz.open(fp) as doc:
                return QPixmap.fromImage(
                    QImage.fromData(doc.load_page(0).get_pixmap(matrix=fitz.Matrix(0.3, 0.3)).tobytes("ppm"))
                )
        except Exception:
            return None
    
    @staticmethod
    def parse_invoice_local(file_path):
        """本地解析发票完整信息（适用于矢量PDF）
        
        对于电子发票PDF，可直接提取文字无需OCR。
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
            "_local_parsed": True,  # 标记为本地解析
        }
        
        try:
            with fitz.open(file_path) as doc:
                # 使用x坐标区分购买方（左边）和销售方（右边）
                buyer_name = ""
                buyer_tax = ""
                seller_name = ""
                seller_tax = ""
                all_text_parts = []
                
                for page in doc:
                    page_width = page.rect.width
                    mid_x = page_width / 2
                    
                    blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)["blocks"]
                    
                    for block in blocks:
                        if "lines" not in block:
                            continue
                        
                        for line in block["lines"]:
                            line_black = ""
                            
                            for span in line["spans"]:
                                text = span["text"]
                                span_bbox = span.get("bbox", [0, 0, 0, 0])
                                span_x = span_bbox[0]
                                color = span.get("color", 0)
                                r = (color >> 16) & 0xFF
                                g = (color >> 8) & 0xFF
                                b = color & 0xFF
                                
                                is_dark = (r < 100 and g < 100 and b < 100)
                                
                                if is_dark:
                                    line_black += text
                                    is_left = span_x < mid_x
                                    
                                    m_company = re.search(r'([^\n\r]{3,50}(?:公司|单位|中心|联络处|处|局|厅|院|所|站|部|协会|基金|集团))', text)
                                    if m_company:
                                        if is_left and not buyer_name:
                                            buyer_name = m_company.group(1).strip()
                                        elif not is_left and not seller_name:
                                            seller_name = m_company.group(1).strip()
                                    
                                    # 提取税号（统一社会信用代码）
                                    # 税号特征：18位字母数字组合
                                    # 排除8位或20位纯数字（发票号码）
                                    m_tax = re.search(r'([A-Za-z0-9]{15,18})', text)
                                    if m_tax:
                                        tax_id = m_tax.group(1)
                                        is_invoice_number = (len(tax_id) in [8, 20]) and tax_id.isdigit()
                                        is_valid_tax = len(tax_id) >= 15 and len(tax_id) <= 18
                                        if is_valid_tax and not is_invoice_number:
                                            if is_left and not buyer_tax:
                                                buyer_tax = tax_id
                                            elif not is_left and not seller_tax:
                                                seller_tax = tax_id
                            
                            if line_black.strip():
                                all_text_parts.append(line_black)
                
                if buyer_name:
                    result["buyer"] = buyer_name
                if buyer_tax:
                    result["buyer_tax_id"] = buyer_tax
                if seller_name:
                    result["seller"] = seller_name
                if seller_tax:
                    result["seller_tax_id"] = seller_tax
                
                text = "\n".join(all_text_parts)
                
                if not text.strip():
                    text = "\n".join([page.get_text() for page in doc])
                
                if not text.strip():
                    return result
                
                # === 金额提取 ===
                # 优先匹配"价税合计"或"小写"后的金额
                m_total = re.search(r'(?:价税合计|小写)[^\d¥￥]*[¥￥]?\s*([0-9,]+\.\d{2})', text)
                if m_total:
                    result["amount"] = float(m_total.group(1).replace(",", ""))
                else:
                    # 回退：提取所有金额，取最大值
                    amounts = re.findall(r'[¥￥]\s*([0-9,]+\.\d{2})', text)
                    if amounts:
                        result["amount"] = max([float(x.replace(",", "")) for x in amounts])
                
                # 不含税金额
                m_without_tax = re.search(r'(?:合\s*计|金\s*额)[^\d¥￥]*[¥￥]?\s*([0-9,]+\.\d{2})', text)
                if m_without_tax:
                    result["amount_without_tax"] = m_without_tax.group(1).replace(",", "")
                
                # 税额
                m_tax = re.search(r'(?:税\s*额)[^\d¥￥]*[¥￥]?\s*([0-9,]+\.\d{2})', text)
                if m_tax:
                    result["tax_amt"] = m_tax.group(1).replace(",", "")
                
                # === 日期提取 ===
                m_date = re.search(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日', text)
                if m_date:
                    result["date"] = f"{m_date.group(1)}-{m_date.group(2).zfill(2)}-{m_date.group(3).zfill(2)}"
                else:
                    # 尝试 YYYY-MM-DD 格式
                    m_date2 = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
                    if m_date2:
                        result["date"] = f"{m_date2.group(1)}-{m_date2.group(2)}-{m_date2.group(3)}"
                
                # === 发票号码 ===
                # 全电发票20位
                m_num20 = re.search(r'发票号[码]?[：:]*\s*(\d{20})', text)
                if m_num20:
                    result["number"] = m_num20.group(1)
                    result["invoice_type"] = "全电发票"
                else:
                    # 传统发票8位
                    m_num8 = re.search(r'发票号[码]?[：:]*\s*(\d{8})\b', text)
                    if m_num8:
                        result["number"] = m_num8.group(1)
                    else:
                        # 财政票据号码（10位）
                        m_receipt_num = re.search(r'票据号[码]?[：:]*\s*(\d{10})', text)
                        if m_receipt_num:
                            result["number"] = m_receipt_num.group(1)
                            result["invoice_type"] = "财政电子票据"
                
                # === 发票代码/票据代码 ===
                if not m_num20:
                    m_code = re.search(r'(?:发票代码|票据代码)[：:]*\s*(\d{8,12})', text)
                    if m_code:
                        result["code"] = m_code.group(1)
                
                # === 校验码 ===（支持20位和6位）
                m_check = re.search(r'校验码[：:\s]*(\d{20}|\d{6}|\d+\s+\d+\s+\d+\s+\d+)', text)
                if m_check:
                    result["check_code"] = m_check.group(1).replace(" ", "")
                
                # === 回退策略（如果区块检测未提取到数据）===
                if not result["buyer"]:
                    m_payer = re.search(r'交款人[：:]*\s*([^\n\r]{2,60})', text)
                    if m_payer:
                        result["buyer"] = m_payer.group(1).strip()
                    else:
                        company_pattern = r'([^\n\r]{3,50}(?:公司|单位|中心|联络处|处|局|厅|院|所|站|部|协会|基金|集团))'
                        companies = re.findall(company_pattern, text)
                        seen = set()
                        unique_companies = []
                        for c in companies:
                            c = c.strip()
                            if c and c not in seen and len(c) > 3:
                                seen.add(c)
                                unique_companies.append(c)
                        if len(unique_companies) >= 1:
                            result["buyer"] = unique_companies[0]
                        if not result["seller"] and len(unique_companies) >= 2:
                            result["seller"] = unique_companies[1]
                
                if not result["seller"]:
                    m_payee = re.search(r'收款单位[（(章）)]*[：:]*\s*([^\n\r]{2,60})', text)
                    if m_payee:
                        result["seller"] = m_payee.group(1).strip()
                
                if not result["buyer_tax_id"] or not result["seller_tax_id"]:
                    tax_ids = re.findall(r'([A-Za-z0-9]{15,20})', text)
                    if len(tax_ids) >= 2:
                        if not result["buyer_tax_id"]:
                            result["buyer_tax_id"] = tax_ids[0]
                        if not result["seller_tax_id"]:
                            result["seller_tax_id"] = tax_ids[1]
                    elif len(tax_ids) == 1 and not result["buyer_tax_id"]:
                        result["buyer_tax_id"] = tax_ids[0]
                
                # === 税率 ===
                m_rate = re.search(r'(?:税率)[：:\s]*(\d{1,2}%|\d{1,2}\.\d+%)', text)
                if m_rate:
                    result["tax_rate"] = m_rate.group(1)
                else:
                    # 尝试从表格中提取
                    rates = re.findall(r'(\d{1,2})%', text)
                    common_rates = [r for r in rates if r in ['0', '1', '3', '5', '6', '9', '13']]
                    if common_rates:
                        result["tax_rate"] = common_rates[0] + "%"
                
                # === 商品名称 ===（匹配以*开头的商品分类或项目名称列的实际内容）
                m_item = re.search(r'\*([^*\n\r]{1,20})\*([^\n\r]{1,30})', text)  # *类别*商品名
                if m_item:
                    result["item_name"] = f"*{m_item.group(1)}*{m_item.group(2).strip()}"
                else:
                    m_item2 = re.search(r'项目名称[\n\r]+([^\n\r]{2,30}?)(?:\s+\d|$)', text)
                    if m_item2 and '规格' not in m_item2.group(1):
                        result["item_name"] = m_item2.group(1).strip()
                
                # === 备注 ===（排除统一社会信用代码等内容）
                m_remark = re.search(r'备\s*注[：:\s]*([^\n\r]{1,100})', text)
                if m_remark:
                    remark_text = m_remark.group(1).strip()
                    if not any(x in remark_text for x in ['统一社会信用', '纳税人识别', '信用代码', '识别号']):
                        result["remark"] = remark_text
                
                # === 机器编号 ===
                m_machine = re.search(r'(?:机器编号|机打代码)[：:\s]*(\d{10,12})', text)
                if m_machine:
                    result["machine_code"] = m_machine.group(1)
                
                # === 发票类型判断 ===
                if not result["invoice_type"]:
                    if "专用发票" in text:
                        result["invoice_type"] = "增值税专用发票"
                    elif "普通发票" in text:
                        result["invoice_type"] = "增值税普通发票"
                    elif "电子发票" in text:
                        result["invoice_type"] = "增值税电子普通发票"
                
        except Exception:
            pass
        
        return result
    
    @staticmethod
    def parse_amount_local(file_path):
        """本地解析发票金额和日期（兼容旧接口）"""
        result = InvoiceHelper.parse_invoice_local(file_path)
        return result.get("amount", 0.0), result.get("date", "")
    
    @staticmethod
    def ocr(fp, ak, sk):
        """执行 OCR 识别（本地解析优先，回退到远程服务）
        
        优先级：本地PDF解析 → 私有OCR服务 → 百度云OCR
        """
        logger = logging.getLogger(__name__)
        s = QSettings("MySoft", "InvoiceMaster")
        private_ocr_url = s.value("private_ocr_url", "")
        
        # 1. 优先尝试本地解析（适用于矢量PDF）
        if fp.lower().endswith('.pdf'):
            try:
                local_result = InvoiceHelper.parse_invoice_local(fp)
                # 如果提取到金额和日期，认为本地解析成功
                if local_result.get("amount", 0) > 0 and local_result.get("date"):
                    logger.info(f"本地解析成功: {os.path.basename(fp)}, 金额: {local_result['amount']}")
                    return local_result
                elif local_result.get("amount", 0) > 0:
                    # 只有金额也可以接受
                    logger.info(f"本地解析部分成功: {os.path.basename(fp)}, 金额: {local_result['amount']}")
                    return local_result
            except Exception as e:
                logger.warning(f"本地解析失败: {str(e)}")
        
        # 2. 尝试私有 OCR 服务
        if private_ocr_url:
            try:
                result = InvoiceHelper._call_private_ocr(fp, private_ocr_url, logger)
                if result:
                    logger.info(f"私有OCR成功: {os.path.basename(fp)}")
                    return result
            except Exception as e:
                logger.warning(f"私有OCR失败: {str(e)}，回退到百度OCR")
        
        # 3. 回退到百度云 OCR
        return InvoiceHelper._call_baidu_ocr(fp, ak, sk, logger)
    
    @staticmethod
    def _call_private_ocr(fp, private_ocr_url, logger):
        """调用私有 PaddleOCR 服务"""
        logger.info(f"尝试私有OCR: {os.path.basename(fp)}")
        
        # 处理 PDF 文件：先转成图片
        if fp.lower().endswith('.pdf'):
            doc = fitz.open(fp)
            page = doc[0]
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            doc.close()
            b = base64.b64encode(img_data).decode()
        else:
            with open(fp, 'rb') as f:
                b = base64.b64encode(f.read()).decode()
        
        # 调用私有 OCR API
        url = f"{private_ocr_url}/ocr/invoice"
        resp = requests.post(url, json={"image": b}, timeout=30)
        
        if resp.status_code != 200:
            raise Exception(f"私有OCR返回错误: {resp.status_code}")
        
        data = resp.json()
        if not data.get("success"):
            raise Exception(f"私有OCR识别失败: {data.get('error', '未知错误')}")
        
        # 转换返回格式
        result = {
            "date": data.get("date", ""),
            "amount": float(data.get("amount", 0) or 0),
            "amount_without_tax": data.get("amount_without_tax", ""),
            "tax_amt": data.get("tax_amt", ""),
            "tax_rate": data.get("tax_rate", ""),
            "seller": data.get("seller", ""),
            "seller_tax_id": data.get("seller_tax_id", ""),
            "buyer": data.get("buyer", ""),
            "buyer_tax_id": data.get("buyer_tax_id", ""),
            "code": data.get("code", ""),
            "number": data.get("number", ""),
            "check_code": data.get("check_code", ""),
            "invoice_type": data.get("invoice_type", ""),
            "item_name": data.get("item_name", ""),
            "remark": data.get("remark", ""),
            "machine_code": data.get("machine_code", ""),
        }
        logger.info(f"私有OCR识别成功: {os.path.basename(fp)}, 金额: {result.get('amount', 0)}")
        return result
    
    @staticmethod
    def _call_baidu_ocr(fp, ak, sk, logger):
        """调用百度云 OCR 服务"""
        if not ak:
            logger.warning("OCR 未配置 API Key")
            return {}
        try:
            logger.info(f"百度OCR识别开始: {os.path.basename(fp)}")
            # 获取 access_token
            token_resp = requests.get(
                f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={ak}&client_secret={sk}"
            ).json()
            if "error" in token_resp:
                logger.error(f"OCR Token获取失败: {token_resp.get('error_description', token_resp.get('error'))}")
                return {}
            t = token_resp.get("access_token")
            if not t:
                logger.error("OCR Token为空")
                return {}
            
            # 处理 PDF 文件
            if fp.lower().endswith('.pdf'):
                doc = fitz.open(fp)
                page = doc[0]
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                doc.close()
                b = base64.b64encode(img_data).decode()
            else:
                with open(fp, 'rb') as f:
                    b = base64.b64encode(f.read()).decode()
            
            # 延迟避免 QPS 限制
            time.sleep(0.6)
            
            r = requests.post(
                f"https://aip.baidubce.com/rest/2.0/ocr/v1/vat_invoice?access_token={t}",
                data={"image": b},
                headers={'content-type': 'application/x-www-form-urlencoded'}
            ).json()
            
            if "error_code" in r:
                logger.error(f"OCR API错误: {r.get('error_code')} - {r.get('error_msg')}")
                return {}
            
            wr = r.get("words_result", {})
            items = wr.get("CommodityName", [])
            item_str = ",".join([x.get("word", "") for x in items]) if isinstance(items, list) else str(items)
            tax_rates = wr.get("CommodityTaxRate", [])
            tax_rate_str = ",".join([x.get("word", "") for x in tax_rates]) if isinstance(tax_rates, list) else str(tax_rates)
            
            result = {
                "date": wr.get("InvoiceDate", ""),
                "amount": float(wr.get("AmountInFiguers", "0") or "0"),
                "amount_without_tax": wr.get("TotalAmount", ""),
                "tax_amt": wr.get("TotalTax", ""),
                "tax_rate": tax_rate_str,
                "seller": wr.get("SellerName", ""),
                "seller_tax_id": wr.get("SellerRegisterNum", ""),
                "buyer": wr.get("PurchaserName", ""),
                "buyer_tax_id": wr.get("PurchaserRegisterNum", ""),
                "code": wr.get("InvoiceCode", ""),
                "number": wr.get("InvoiceNum", ""),
                "check_code": wr.get("CheckCode", ""),
                "invoice_type": wr.get("InvoiceType", ""),
                "item_name": item_str,
                "remark": wr.get("Remarks", ""),
                "machine_code": wr.get("MachineCode", ""),
            }
            logger.info(f"百度OCR识别成功: {os.path.basename(fp)}, 金额: {result.get('amount', 0)}")
            return result
        except Exception as e:
            logger.error(f"百度OCR识别失败: {os.path.basename(fp)}, 错误: {str(e)}")
            return {}
