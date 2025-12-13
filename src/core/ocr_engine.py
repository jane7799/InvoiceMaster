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
        except:
            return None
    
    @staticmethod
    def parse_amount_local(file_path):
        """本地解析发票金额和日期"""
        amount = 0.0
        date = ""
        try:
            with fitz.open(file_path) as doc:
                text = "".join([page.get_text() for page in doc])
                m_total = re.search(r'(小写).*?[¥￥]?\s*([0-9,]+\.\d{2})', text)
                if m_total:
                    amount = float(m_total.group(2).replace(",", ""))
                else:
                    amounts = re.findall(r'[¥￥]\s*([0-9,]+\.\d{2})', text)
                    if amounts:
                        amount = max([float(x.replace(",", "")) for x in amounts])
                m_date = re.search(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日', text)
                if m_date:
                    date = f"{m_date.group(1)}-{m_date.group(2).zfill(2)}-{m_date.group(3).zfill(2)}"
        except:
            pass
        return amount, date
    
    @staticmethod
    def ocr(fp, ak, sk):
        """执行 OCR 识别（优先私有服务，回退百度云）"""
        logger = logging.getLogger(__name__)
        s = QSettings("MySoft", "InvoiceMaster")
        private_ocr_url = s.value("private_ocr_url", "")
        
        # 优先尝试私有 OCR 服务
        if private_ocr_url:
            try:
                result = InvoiceHelper._call_private_ocr(fp, private_ocr_url, logger)
                if result:
                    logger.info(f"私有OCR成功: {os.path.basename(fp)}")
                    return result
            except Exception as e:
                logger.warning(f"私有OCR失败: {str(e)}，回退到百度OCR")
        
        # 回退到百度云 OCR
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
