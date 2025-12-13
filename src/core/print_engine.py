"""
打印引擎模块
提供 PDF 打印功能
"""
import os
import logging
import fitz  # PyMuPDF

from PyQt6.QtGui import QImage, QPainter, QPageLayout, QTransform
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtCore import Qt


class PrinterEngine:
    """打印引擎"""
    
    @staticmethod
    def print_pdf(pdf_path, printer, copies=1, force_rotate=False):
        """
        打印 PDF 文件
        
        Args:
            pdf_path: PDF 文件路径
            printer: QPrinter 对象
            copies: 打印份数
            force_rotate: 是否强制旋转 90 度
            
        Returns:
            (success: bool, message: str)
        """
        logger = logging.getLogger(__name__)
        logger.info(f"开始打印: {os.path.basename(pdf_path)}, 份数: {copies}, DPI: 600")
        
        try:
            # 设置高质量打印参数
            printer.setCopyCount(copies)
            printer.setResolution(600)
            printer.setFullPage(True)
            
            with fitz.open(pdf_path) as doc:
                painter = QPainter()
                if not painter.begin(printer):
                    logger.error("无法启动打印任务")
                    return False, "无法启动打印任务"
                
                for i, page in enumerate(doc):
                    if i > 0:
                        printer.newPage()
                    
                    # 高质量渲染
                    pix = page.get_pixmap(matrix=fitz.Matrix(4.0, 4.0), alpha=False)
                    img = QImage.fromData(pix.tobytes("ppm"))
                    
                    # 纵向布局
                    printer.setPageOrientation(QPageLayout.Orientation.Portrait)
                    
                    if force_rotate:
                        transform = QTransform()
                        transform.rotate(90)
                        img = img.transformed(transform)
                    
                    page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
                    
                    try:
                        safe_rect = printer.pageLayout().paintRectPixels(printer.resolution())
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
            
            logger.info(f"打印任务发送成功: {os.path.basename(pdf_path)}")
            return True, "发送成功"
        except Exception as e:
            logger.error(f"打印失败: {os.path.basename(pdf_path)}, 错误: {str(e)}", exc_info=True)
            return False, str(e)
