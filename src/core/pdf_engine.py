
import os
import fitz  # PyMuPDF
import logging

class PDFEngine:
    SIZES = {"A4":(595,842), "A5":(420,595), "B5":(499,709)}
    @staticmethod
    def merge(files, mode="1x1", paper="A4", orient="V", cutline=True, out_path=None):
        doc = fitz.open(); bw, bh = PDFEngine.SIZES.get(paper, (595,842))
        
        # [V3.3.0] 永远纵向
        PW, PH = (bw, bh) 
        
        cells = []
        if mode == "1x1":
            cells = [(0, 0, PW, PH)] 
        elif mode == "1x2":
            cells = [(0, 0, PW, PH/2), (0, PH/2, PW, PH/2)]
        elif mode == "2x2":
            mw, mh = PW/2, PH/2
            cells = [(0, 0, mw, mh), (mw, 0, mw, mh), (0, mh, mw, mh), (mw, mh, mw, mh)]
            
        if not files: doc.new_page(width=PW, height=PH)
        PADDING = 40
        chunk_size = len(cells)
        try:
            for i in range(0, len(files), chunk_size):
                chunk = files[i:i+chunk_size]; pg = doc.new_page(width=PW, height=PH)
                for j, f in enumerate(chunk):
                    if j >= len(cells): break
                    try:
                        cx, cy, cw, ch = cells[j]
                        rotate_angle = -90 if orient == "H" else 0
                        target_rect = fitz.Rect(cx + PADDING, cy + PADDING, cx + cw - PADDING, cy + ch - PADDING)
                        
                        # 检查文件类型
                        if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                            # 图片文件:直接插入图片
                            pg.insert_image(target_rect, filename=f, keep_proportion=True, rotate=rotate_angle)
                        else:
                            # PDF文件:使用 show_pdf_page
                            with fitz.open(f) as src_doc:
                                pg.show_pdf_page(target_rect, src_doc, 0, keep_proportion=True, rotate=rotate_angle)
                    except Exception as e:
                        logger = logging.getLogger(__name__)
                        logger.error(f"处理文件失败 {os.path.basename(f)}: {str(e)}")
                        pass
                if cutline:
                    s = pg.new_shape(); s.draw_rect(fitz.Rect(0,0,0,0)) 
                    if mode == "1x2":
                        s.draw_line(fitz.Point(0, PH/2), fitz.Point(PW, PH/2)) 
                    elif mode == "2x2":
                        s.draw_line(fitz.Point(PW/2, 0), fitz.Point(PW/2, PH)) 
                        s.draw_line(fitz.Point(0, PH/2), fitz.Point(PW, PH/2)) 
                    s.finish(color=(0,0,0), width=0.5, dashes=[4,4], stroke_opacity=0.6); s.commit(overlay=True)
            if out_path: doc.save(out_path)
            return doc if not out_path else None
        finally:
            if out_path: doc.close()
