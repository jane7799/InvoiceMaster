"""
PDF 引擎模块
提供 PDF 合并和布局功能
"""
import os
import logging
import fitz  # PyMuPDF


class PDFEngine:
    """PDF 处理引擎"""
    
    SIZES = {"A4": (595, 842), "A5": (420, 595), "B5": (499, 709)}
    
    @staticmethod
    def merge(files, mode="1x1", paper="A4", orient="V", cutline=True, out_path=None):
        """
        合并多个 PDF/图片文件到一个 PDF
        
        Args:
            files: 文件路径列表
            mode: 布局模式 (1x1, 1x2, 2x2)
            paper: 纸张大小 (A4, A5, B5)
            orient: 方向 (V=纵向, H=横向)
            cutline: 是否显示裁剪线
            out_path: 输出路径
            
        Returns:
            如果 out_path 为 None，返回 fitz.Document 对象
            如果指定了 out_path，保存并返回 None
        """
        logger = logging.getLogger(__name__)
        doc = fitz.open()
        bw, bh = PDFEngine.SIZES.get(paper, (595, 842))
        
        # 纵向布局
        PW, PH = (bw, bh)
        
        # 计算单元格布局
        cells = []
        if mode == "1x1":
            cells = [(0, 0, PW, PH)]
        elif mode == "1x2":
            cells = [(0, 0, PW, PH/2), (0, PH/2, PW, PH/2)]
        elif mode == "2x2":
            mw, mh = PW/2, PH/2
            cells = [(0, 0, mw, mh), (mw, 0, mw, mh), (0, mh, mw, mh), (mw, mh, mw, mh)]
        
        if not files:
            doc.new_page(width=PW, height=PH)
        
        PADDING = 40
        chunk_size = len(cells)
        
        try:
            for i in range(0, len(files), chunk_size):
                chunk = files[i:i+chunk_size]
                pg = doc.new_page(width=PW, height=PH)
                
                for j, f in enumerate(chunk):
                    if j >= len(cells):
                        break
                    try:
                        cx, cy, cw, ch = cells[j]
                        rotate_angle = -90 if orient == "H" else 0
                        target_rect = fitz.Rect(cx + PADDING, cy + PADDING, cx + cw - PADDING, cy + ch - PADDING)
                        
                        # 根据文件类型插入
                        if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                            pg.insert_image(target_rect, filename=f, keep_proportion=True, rotate=rotate_angle)
                        else:
                            with fitz.open(f) as src_doc:
                                pg.show_pdf_page(target_rect, src_doc, 0, keep_proportion=True, rotate=rotate_angle)
                    except Exception as e:
                        logger.error(f"处理文件失败 {os.path.basename(f)}: {str(e)}")
                
                # 绘制裁剪线
                if cutline:
                    s = pg.new_shape()
                    s.draw_rect(fitz.Rect(0, 0, 0, 0))
                    if mode == "1x2":
                        s.draw_line(fitz.Point(0, PH/2), fitz.Point(PW, PH/2))
                    elif mode == "2x2":
                        s.draw_line(fitz.Point(PW/2, 0), fitz.Point(PW/2, PH))
                        s.draw_line(fitz.Point(0, PH/2), fitz.Point(PW, PH/2))
                    s.finish(color=(0, 0, 0), width=0.5, dashes=[4, 4], stroke_opacity=0.6)
                    s.commit(overlay=True)
            
            if out_path:
                doc.save(out_path)
                return None
            return doc
        finally:
            if out_path:
                doc.close()
