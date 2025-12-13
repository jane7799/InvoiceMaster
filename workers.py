"""
异步工作线程模块
用于处理耗时的 OCR、PDF 合并、打印操作，避免 UI 卡顿
"""
import os
import base64
import logging
import time
import requests
import fitz  # PyMuPDF

from PyQt6.QtCore import QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QImage, QPainter, QPageLayout, QTransform
from PyQt6.QtWidgets import QApplication
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtCore import Qt


class OcrWorker(QThread):
    """OCR 异步处理线程"""
    
    # 信号定义
    progress = pyqtSignal(int, int, str)  # current, total, filename
    result = pyqtSignal(int, dict)  # index, ocr_result
    error = pyqtSignal(int, str)  # index, error_message
    finished_all = pyqtSignal()  # 全部完成
    
    def __init__(self, files_with_index, ak, sk, parent=None):
        """
        初始化 OCR Worker
        
        Args:
            files_with_index: list of (index, file_path) tuples
            ak: 百度 API Key
            sk: 百度 Secret Key
        """
        super().__init__(parent)
        self.files_with_index = files_with_index
        self.ak = ak
        self.sk = sk
        self._is_cancelled = False
        self.logger = logging.getLogger(__name__)
        
    def cancel(self):
        """取消处理"""
        self._is_cancelled = True
        
    def run(self):
        """执行 OCR 处理"""
        total = len(self.files_with_index)
        s = QSettings("MySoft", "InvoiceMaster")
        private_ocr_url = s.value("private_ocr_url", "")
        
        for i, (idx, fp) in enumerate(self.files_with_index):
            if self._is_cancelled:
                break
                
            filename = os.path.basename(fp)
            self.progress.emit(i + 1, total, filename)
            
            try:
                # 优先尝试私有 OCR
                result = None
                if private_ocr_url:
                    try:
                        result = self._call_private_ocr(fp, private_ocr_url)
                        if result:
                            self.logger.info(f"私有OCR成功: {filename}")
                    except Exception as e:
                        self.logger.warning(f"私有OCR失败: {str(e)}，回退到百度OCR")
                
                # 回退到百度 OCR
                if not result:
                    result = self._call_baidu_ocr(fp)
                
                self.result.emit(idx, result if result else {})
                
            except Exception as e:
                self.logger.error(f"OCR处理失败: {filename}, 错误: {str(e)}")
                self.error.emit(idx, str(e))
                
        self.finished_all.emit()
    
    def _call_private_ocr(self, fp, private_ocr_url):
        """调用私有 PaddleOCR 服务"""
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
        return {
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
    
    def _call_baidu_ocr(self, fp):
        """调用百度云 OCR 服务"""
        if not self.ak:
            self.logger.warning("OCR 未配置 API Key")
            return {}
            
        # 获取 access_token
        token_resp = requests.get(
            f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.ak}&client_secret={self.sk}"
        ).json()
        
        if "error" in token_resp:
            raise Exception(f"Token获取失败: {token_resp.get('error_description', token_resp.get('error'))}")
        
        t = token_resp.get("access_token")
        if not t:
            raise Exception("Token为空")
        
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
            raise Exception(f"API错误: {r.get('error_code')} - {r.get('error_msg')}")
        
        wr = r.get("words_result", {})
        items = wr.get("CommodityName", [])
        item_str = ",".join([x.get("word", "") for x in items]) if isinstance(items, list) else str(items)
        tax_rates = wr.get("CommodityTaxRate", [])
        tax_rate_str = ",".join([x.get("word", "") for x in tax_rates]) if isinstance(tax_rates, list) else str(tax_rates)
        
        return {
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


class PdfWorker(QThread):
    """PDF 合并异步处理线程"""
    
    progress = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal(str)  # output_path
    error = pyqtSignal(str)  # error_message
    
    SIZES = {"A4": (595, 842), "A5": (420, 595), "B5": (499, 709)}
    
    def __init__(self, files, mode="1x1", paper="A4", orient="V", cutline=True, out_path=None, parent=None):
        super().__init__(parent)
        self.files = files
        self.mode = mode
        self.paper = paper
        self.orient = orient
        self.cutline = cutline
        self.out_path = out_path or os.path.expanduser("~/Desktop/Print_Job.pdf")
        self._is_cancelled = False
        self.logger = logging.getLogger(__name__)
        
    def cancel(self):
        self._is_cancelled = True
        
    def run(self):
        try:
            doc = fitz.open()
            bw, bh = self.SIZES.get(self.paper, (595, 842))
            PW, PH = (bw, bh)
            PADDING = 40
            
            cells = []
            if self.mode == "1x1":
                cells = [(0, 0, PW, PH)]
            elif self.mode == "1x2":
                cells = [(0, 0, PW, PH/2), (0, PH/2, PW, PH/2)]
            elif self.mode == "2x2":
                mw, mh = PW/2, PH/2
                cells = [(0, 0, mw, mh), (mw, 0, mw, mh), (0, mh, mw, mh), (mw, mh, mw, mh)]
            
            if not self.files:
                doc.new_page(width=PW, height=PH)
            
            chunk_size = len(cells)
            total_chunks = (len(self.files) + chunk_size - 1) // chunk_size
            
            for i in range(0, len(self.files), chunk_size):
                if self._is_cancelled:
                    doc.close()
                    return
                    
                chunk = self.files[i:i+chunk_size]
                pg = doc.new_page(width=PW, height=PH)
                
                self.progress.emit(i // chunk_size + 1, total_chunks)
                
                for j, f in enumerate(chunk):
                    if j >= len(cells):
                        break
                    try:
                        cx, cy, cw, ch = cells[j]
                        rotate_angle = -90 if self.orient == "H" else 0
                        target_rect = fitz.Rect(cx + PADDING, cy + PADDING, cx + cw - PADDING, cy + ch - PADDING)
                        
                        if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                            pg.insert_image(target_rect, filename=f, keep_proportion=True, rotate=rotate_angle)
                        else:
                            with fitz.open(f) as src_doc:
                                pg.show_pdf_page(target_rect, src_doc, 0, keep_proportion=True, rotate=rotate_angle)
                    except Exception as e:
                        self.logger.error(f"处理文件失败 {os.path.basename(f)}: {str(e)}")
                
                if self.cutline:
                    s = pg.new_shape()
                    s.draw_rect(fitz.Rect(0, 0, 0, 0))
                    if self.mode == "1x2":
                        s.draw_line(fitz.Point(0, PH/2), fitz.Point(PW, PH/2))
                    elif self.mode == "2x2":
                        s.draw_line(fitz.Point(PW/2, 0), fitz.Point(PW/2, PH))
                        s.draw_line(fitz.Point(0, PH/2), fitz.Point(PW, PH/2))
                    s.finish(color=(0, 0, 0), width=0.5, dashes=[4, 4], stroke_opacity=0.6)
                    s.commit(overlay=True)
            
            doc.save(self.out_path)
            doc.close()
            self.finished.emit(self.out_path)
            
        except Exception as e:
            self.logger.error(f"PDF合并失败: {str(e)}")
            self.error.emit(str(e))


class PrintWorker(QThread):
    """打印异步处理线程"""
    
    progress = pyqtSignal(int, int)  # current_page, total_pages
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, pdf_path, printer, copies=1, force_rotate=False, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.printer = printer
        self.copies = copies
        self.force_rotate = force_rotate
        self.logger = logging.getLogger(__name__)
        
    def run(self):
        try:
            self.logger.info(f"开始打印: {os.path.basename(self.pdf_path)}, 份数: {self.copies}")
            
            self.printer.setCopyCount(self.copies)
            self.printer.setResolution(600)
            self.printer.setFullPage(True)
            
            with fitz.open(self.pdf_path) as doc:
                total_pages = len(doc)
                painter = QPainter()
                
                if not painter.begin(self.printer):
                    self.finished.emit(False, "无法启动打印任务")
                    return
                
                for i, page in enumerate(doc):
                    self.progress.emit(i + 1, total_pages)
                    
                    if i > 0:
                        self.printer.newPage()
                    
                    pix = page.get_pixmap(matrix=fitz.Matrix(4.0, 4.0), alpha=False)
                    img = QImage.fromData(pix.tobytes("ppm"))
                    
                    self.printer.setPageOrientation(QPageLayout.Orientation.Portrait)
                    
                    if self.force_rotate:
                        transform = QTransform()
                        transform.rotate(90)
                        img = img.transformed(transform)
                    
                    page_rect = self.printer.pageRect(QPrinter.Unit.DevicePixel)
                    
                    try:
                        safe_rect = self.printer.pageLayout().paintRectPixels(self.printer.resolution())
                    except:
                        safe_rect = page_rect
                    
                    target_w = int(safe_rect.width())
                    target_h = int(safe_rect.height())
                    scaled_img = img.scaled(
                        target_w, target_h,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    
                    x = int(safe_rect.x() + (safe_rect.width() - scaled_img.width()) / 2)
                    y = int(safe_rect.y() + (safe_rect.height() - scaled_img.height()) / 2)
                    
                    painter.drawImage(x, y, scaled_img)
                
                painter.end()
            
            self.logger.info(f"打印任务发送成功: {os.path.basename(self.pdf_path)}")
            self.finished.emit(True, "发送成功")
            
        except Exception as e:
            self.logger.error(f"打印失败: {str(e)}", exc_info=True)
            self.finished.emit(False, str(e))
