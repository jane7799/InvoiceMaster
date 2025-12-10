import sys
import os
import re
import datetime
import base64
import time
import requests
import pandas as pd
import fitz  # PyMuPDF

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QListWidget, QListWidgetItem, QMessageBox, QSplitter,
                             QComboBox, QSpinBox, QGroupBox, QSplashScreen, 
                             QDialog, QLineEdit, QFormLayout, QFrame, QCheckBox,
                             QRadioButton, QButtonGroup, QAbstractItemView, 
                             QGraphicsDropShadowEffect, QSizePolicy, QMenu, QScrollArea)
from PyQt6.QtCore import Qt, QSettings, QSize, QMimeData, pyqtSignal, QByteArray, QRectF, QPointF, QTimer
from PyQt6.QtGui import QPixmap, QIcon, QDragEnterEvent, QDropEvent, QImage, QColor, QPainter, QPalette, QPen, QFont, QAction
from PyQt6.QtPrintSupport import QPrinterInfo, QPageSetupDialog, QPrinter

# ==========================================
# 0. SVG 图标库
# ==========================================
class Icons:
    _SVGS = {
        "upload": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>""",
        "settings": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>""",
        "trash": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>""",
        "excel": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>""",
        "print": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>""",
        "layout_1x1": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2"><rect x="5" y="4" width="14" height="16" rx="1"/></svg>""",
        "layout_1x2": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2"><rect x="2" y="5" width="9" height="14" rx="1"/><rect x="13" y="5" width="9" height="14" rx="1"/></svg>""",
        "layout_2x2": """<svg viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2"><rect x="4" y="4" width="7" height="7" rx="1"/><rect x="13" y="4" width="7" height="7" rx="1"/><rect x="4" y="13" width="7" height="7" rx="1"/><rect x="13" y="13" width="7" height="7" rx="1"/></svg>"""
    }
    @staticmethod
    def get(name, color="#555"):
        return QIcon(QPixmap.fromImage(QImage.fromData(QByteArray(Icons._SVGS.get(name,"").format(c=color).encode()))))

# ==========================================
# 1. 样式与主题
# ==========================================
class ThemeManager:
    CSS_LIGHT = """
    QMainWindow { background-color: #f0f2f5; }
    QWidget { color: #333; font-family: -apple-system, "Segoe UI", sans-serif; font-size: 13px; }
    
    QFrame#Card { background-color: white; border: 1px solid #e1e4e8; border-radius: 12px; }
    
    QPushButton { background-color: white; border: 1px solid #d1d5da; border-radius: 6px; padding: 6px; }
    QPushButton:hover { background-color: #f6f8fa; border-color: #0366d6; color: #0366d6; }
    QPushButton:checked { background-color: #e1f0fa; border-color: #0366d6; color: #0366d6; font-weight: bold; }
    
    /* 重点优化：排版按钮样式 */
    QPushButton#LayoutBtn { 
        background-color: #f9f9f9; border: 1px solid #dcdfe6; border-radius: 8px; 
    }
    QPushButton#LayoutBtn:hover { 
        background-color: #ecf5ff; border-color: #c6e2ff; 
    }
    QPushButton#LayoutBtn:checked { 
        background-color: #e6f7ff; border: 2px solid #007AFF; 
    }

    QPushButton#PrimaryBtn { background-color: #007AFF; border: none; color: white; font-weight: bold; font-size: 14px; }
    QPushButton#PrimaryBtn:hover { background-color: #0062cc; }
    QPushButton#DangerBtn { color: #d73a49; }
    
    QListWidget { background-color: white; border: 1px solid #e1e4e8; border-radius: 8px; outline: none; }
    QListWidget::item:selected { background-color: #f1f8ff; border-left: 4px solid #0366d6; color: #0366d6; }
    
    QLineEdit, QComboBox, QSpinBox { border: 1px solid #d1d5da; border-radius: 4px; padding: 5px; background: white; }
    QScrollArea { border: none; background-color: #525659; }
    """
    
    CSS_DARK = """
    QMainWindow { background-color: #1e1e1e; }
    QWidget { color: #ccc; font-family: -apple-system, sans-serif; font-size: 13px; }
    QFrame#Card { background-color: #252526; border: 1px solid #333; border-radius: 12px; }
    QPushButton { background-color: #333; border: 1px solid #444; border-radius: 6px; padding: 6px; color: #ccc; }
    QPushButton:hover { background-color: #3e3e3e; border-color: #007AFF; color: white; }
    
    /* 暗黑模式下的排版按钮 */
    QPushButton#LayoutBtn { background-color: #2d2d2d; border: 1px solid #444; }
    QPushButton#LayoutBtn:checked { background-color: #004080; border: 2px solid #007AFF; }

    QPushButton#PrimaryBtn { background-color: #007AFF; border: none; color: white; font-weight: bold; }
    QListWidget { background-color: #1e1e1e; border: 1px solid #333; border-radius: 8px; outline: none; }
    QListWidget::item:selected { background-color: #004080; border-left: 4px solid #007AFF; color: white; }
    QLineEdit, QComboBox, QSpinBox { border: 1px solid #444; border-radius: 4px; padding: 5px; background: #252526; color: white; }
    QScrollArea { border: none; background-color: #2d2d30; }
    """
    
    @staticmethod
    def apply(app, mode):
        if mode == "Auto": mode = "Dark" if QApplication.palette().color(QPalette.ColorRole.Window).lightness() < 128 else "Light"
        app.setStyleSheet(ThemeManager.CSS_DARK if mode == "Dark" else ThemeManager.CSS_LIGHT)
        return "#ffffff" if mode == "Dark" else "#555555"

# ==========================================
# 2. 核心：Word式滚动预览组件
# ==========================================
class WordPreviewArea(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setStyleSheet("background-color: #525659;") 
        self.container = QWidget(); self.container.setStyleSheet("background-color: transparent;")
        self.layout = QVBoxLayout(self.container)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.layout.setSpacing(20); self.layout.setContentsMargins(20, 20, 20, 20)
        self.setWidget(self.container)
        
        self.placeholder = QLabel("💡 暂无内容\n请在左侧添加发票")
        self.placeholder.setStyleSheet("color: #aaa; font-size: 16px; font-weight: bold;")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.placeholder)

    def show_pages(self, page_images):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        if not page_images: self.layout.addWidget(self.placeholder); return

        for i, img in enumerate(page_images):
            page_lbl = QLabel()
            pix = QPixmap.fromImage(img)
            view_width = self.width() - 60
            if view_width > 800: view_width = 800
            if view_width < 300: view_width = 300
            
            scaled_pix = pix.scaledToWidth(view_width, Qt.TransformationMode.SmoothTransformation)
            page_lbl.setPixmap(scaled_pix)
            
            shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(20); shadow.setColor(QColor(0, 0, 0, 150)); shadow.setOffset(0, 5)
            page_lbl.setGraphicsEffect(shadow)
            
            info_lbl = QLabel(f"Page {i+1}")
            info_lbl.setStyleSheet("color: #aaa; font-size: 10px; margin-bottom: 5px;")
            info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(page_lbl); self.layout.addWidget(info_lbl)

# ==========================================
# 3. 核心引擎
# ==========================================
class PDFEngine:
    SIZES = {"A4":(595,842), "A5":(420,595), "B5":(499,709)}
    @staticmethod
    def merge(files, mode="1x1", paper="A4", cutline=True, out_path=None):
        doc = fitz.open(); base_w, base_h = PDFEngine.SIZES.get(paper, (595,842))
        if mode == "1x2": pw, ph = base_h, base_w 
        else: pw, ph = base_w, base_h
        
        rects = [fitz.Rect(20,20,pw-20,ph-20)]
        if mode == "1x2": rects = [fitz.Rect(20,20,pw/2-10,ph-20), fitz.Rect(pw/2+10,20,pw-20,ph-20)]
        elif mode == "2x2": mw,mh=pw/2,ph/2; rects=[fitz.Rect(20,20,mw-10,mh-10), fitz.Rect(mw+10,20,pw-20,mh-10), fitz.Rect(20,mh+10,mw-10,ph-20), fitz.Rect(mw+10,mh+10,pw-20,ph-20)]
        
        if not files: doc.new_page(width=pw, height=ph)
        
        for i, f in enumerate(files):
            if i % len(rects) == 0:
                pg = doc.new_page(width=pw, height=ph)
                if cutline:
                    s = pg.new_shape(); s.draw_line(fitz.Point(pw/2,0), fitz.Point(pw/2,ph))
                    if mode=="2x2": s.draw_line(fitz.Point(0,ph/2), fitz.Point(pw,ph/2))
                    s.finish(color=(0.8,0.8,0.8), dashes=[2,2]); s.commit()
            try: pg.show_pdf_page(rects[i%len(rects)], fitz.open(f), 0)
            except: pass
            
        if out_path: doc.save(out_path); doc.close(); return None
        else: return doc

class InvoiceHelper:
    @staticmethod
    def thumb(fp):
        try: return QPixmap.fromImage(QImage.fromData(fitz.open(fp).load_page(0).get_pixmap(matrix=fitz.Matrix(0.3,0.3)).tobytes("ppm")))
        except: return Icons.get("file", "#ccc").pixmap(100,100)
    @staticmethod
    def ocr(fp, ak, sk):
        if not ak: return {}
        try:
            t = requests.get(f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={ak}&client_secret={sk}").json().get("access_token")
            with open(fp,'rb') as f: b = base64.b64encode(f.read()).decode()
            r = requests.post(f"https://aip.baidubce.com/rest/2.0/ocr/v1/vat_invoice?access_token={t}", data={"image":b}, headers={'content-type':'application/x-www-form-urlencoded'}).json()
            return r.get("words_result", {})
        except: return {}

# ==========================================
# 4. UI 组件
# ==========================================
class Card(QFrame):
    def __init__(self):
        super().__init__(); self.setObjectName("Card")
        eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(15); eff.setColor(QColor(0,0,0,15)); eff.setOffset(0,2); self.setGraphicsEffect(eff)

class DragArea(QLabel):
    dropped = pyqtSignal(list)
    def __init__(self):
        super().__init__(); self.setAlignment(Qt.AlignmentFlag.AlignCenter); self.setAcceptDrops(True); self.setMinimumHeight(100)
        self.setStyleSheet("border: 2px dashed #cfd8dc; border-radius: 8px; background: transparent;")
    def upd(self, c): self.setPixmap(Icons.get("upload", c).pixmap(48,48))
    def dragEnterEvent(self, e): e.accept()
    def dropEvent(self, e): self.dropped.emit([u.toLocalFile() for u in e.mimeData().urls() if u.toLocalFile().lower().endswith(('.pdf','.jpg','.png'))])
    def mousePressEvent(self, e): 
        fs, _ = QFileDialog.getOpenFileNames(self, "Add", "", "Files (*.pdf *.jpg *.png)")
        if fs: self.dropped.emit(fs)

class SettingsDlg(QDialog):
    def __init__(self, parent):
        super().__init__(parent); self.setWindowTitle("设置"); self.resize(450, 250); lay = QFormLayout(self)
        s = QSettings("MySoft", "InvoiceMaster")
        self.cb_th = QComboBox(); self.cb_th.addItems(["Auto", "Light", "Dark"]); self.cb_th.setCurrentText(s.value("theme", "Auto"))
        self.cb_th.currentTextChanged.connect(parent.change_theme)
        lay.addRow("外观主题:", self.cb_th)
        link = QLabel('<a href="https://console.bce.baidu.com">点击申请百度OCR Key (免费)</a>'); link.setOpenExternalLinks(True); link.setStyleSheet("color:#007AFF")
        lay.addRow("", link)
        self.ak = QLineEdit(s.value("ak","")); self.ak.setPlaceholderText("API Key")
        self.sk = QLineEdit(s.value("sk","")); self.sk.setEchoMode(QLineEdit.EchoMode.Password); self.sk.setPlaceholderText("Secret Key")
        lay.addRow("API Key:", self.ak); lay.addRow("Secret Key:", self.sk)
        btn = QPushButton("保存配置"); btn.setObjectName("PrimaryBtn"); btn.clicked.connect(self.save); lay.addRow("", btn)
    def save(self):
        s = QSettings("MySoft", "InvoiceMaster"); s.setValue("ak", self.ak.text()); s.setValue("sk", self.sk.text()); s.setValue("theme", self.cb_th.currentText()); self.accept()

# ==========================================
# 5. 主窗口
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # [NEW] 标题栏增加作者署名
        self.setWindowTitle("InvoiceMaster V17 - Created by 会钓鱼的猫")
        self.resize(1350, 850)
        self.data = []
        self.theme_c = "#555"
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.generate_realtime_preview)
        
        ThemeManager.apply(QApplication.instance(), "Auto")
        self.init_ui()
        self.change_theme(QSettings("MySoft", "InvoiceMaster").value("theme", "Auto"))

    def init_ui(self):
        main = QWidget(); self.setCentralWidget(main)
        layout = QHBoxLayout(main); layout.setContentsMargins(15,15,15,15); layout.setSpacing(15)

        # === LEFT COLUMN: 列表 ===
        left = QWidget(); left.setFixedWidth(280); lv = QVBoxLayout(left); lv.setContentsMargins(0,0,0,0)
        self.drag = DragArea(); self.drag.dropped.connect(self.add_files)
        self.list = QListWidget(); self.list.setIconSize(QSize(40,50)); self.list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu); self.list.customContextMenuRequested.connect(self.ctx_menu)
        
        tb = QHBoxLayout() 
        self.btn_set = QPushButton(" 设置"); self.btn_set.clicked.connect(lambda: SettingsDlg(self).exec())
        self.btn_del = QPushButton(""); self.btn_del.setToolTip("删除选中"); self.btn_del.clicked.connect(self.del_sel)
        self.btn_clr = QPushButton(" 清空"); self.btn_clr.setObjectName("DangerBtn"); self.btn_clr.clicked.connect(self.clear)
        tb.addWidget(self.btn_set); tb.addStretch(); tb.addWidget(self.btn_del); tb.addWidget(self.btn_clr)
        lv.addWidget(self.drag); lv.addWidget(QLabel("发票清单:", objectName="Title")); lv.addWidget(self.list); lv.addLayout(tb)
        
        # [NEW] 底部添加作者标签
        author_lbl = QLabel("© Designed by 会钓鱼的猫"); author_lbl.setStyleSheet("color: #aaa; font-size: 11px; margin-top: 5px;")
        author_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lv.addWidget(author_lbl)

        # === MIDDLE COLUMN: Word Preview ===
        mid = QWidget(); mv = QVBoxLayout(mid); mv.setContentsMargins(0,0,0,0); mv.setSpacing(0)
        # [CHANGED] 移除了顶部的文字标题，保持干净
        self.word_preview = WordPreviewArea()
        mv.addWidget(self.word_preview)

        # === RIGHT COLUMN: 控制面板 ===
        right = QWidget(); right.setFixedWidth(340); rv = QVBoxLayout(right); rv.setContentsMargins(0,0,0,0)

        # 打印设置卡片
        c2 = Card(); l2 = QVBoxLayout(c2); l2.setSpacing(12)
        l2.addWidget(QLabel("🖨️ 打印设置", objectName="Title"))
        
        r_pr = QHBoxLayout(); self.cb_pr = QComboBox(); self.cb_pr.addItem("🖥️ 仅生成 PDF")
        for p in QPrinterInfo.availablePrinters(): self.cb_pr.addItem(f"🖨️ {p.printerName()}")
        btn_prop = QPushButton("属性"); btn_prop.setFixedWidth(50); btn_prop.clicked.connect(lambda: QPageSetupDialog(QPrinter(), self).exec())
        r_pr.addWidget(self.cb_pr); r_pr.addWidget(btn_prop); l2.addLayout(r_pr)

        r_cp = QHBoxLayout(); self.sp_cpy = QSpinBox(); self.sp_cpy.setRange(1,99); self.sp_cpy.setSuffix(" 份")
        self.cb_pap = QComboBox(); self.cb_pap.addItems(["A4", "A5", "B5"]); self.cb_pap.currentTextChanged.connect(self.trigger_refresh)
        r_cp.addWidget(QLabel("份数:")); r_cp.addWidget(self.sp_cpy); r_cp.addWidget(QLabel("纸张:")); r_cp.addWidget(self.cb_pap); l2.addLayout(r_cp)
        
        # [NEW] 美化后的排版按钮 (使用 LayoutBtn 样式)
        l2.addWidget(QLabel("排版模式:"))
        rm = QHBoxLayout(); 
        self.b1=QPushButton(""); self.b1.setObjectName("LayoutBtn"); self.b1.setToolTip("单张 (1x1)")
        self.b2=QPushButton(""); self.b2.setObjectName("LayoutBtn"); self.b2.setToolTip("平铺 (1x2)")
        self.b4=QPushButton(""); self.b4.setObjectName("LayoutBtn"); self.b4.setToolTip("田字 (2x2)")
        
        for b in [self.b1, self.b2, self.b4]: b.setCheckable(True); b.setFixedSize(70, 50); b.setIconSize(QSize(32,32))
        self.b2.setChecked(True)
        grp=QButtonGroup(self); grp.addButton(self.b1); grp.addButton(self.b2); grp.addButton(self.b4)
        rm.addWidget(self.b1); rm.addWidget(self.b2); rm.addWidget(self.b4); rm.addStretch(); l2.addLayout(rm)

        r_dir = QHBoxLayout(); self.rd_p = QRadioButton("纵向"); self.rd_l = QRadioButton("横向"); self.rd_l.setChecked(True)
        self.rd_p.toggled.connect(self.trigger_refresh); self.rd_l.toggled.connect(self.trigger_refresh)
        r_dir.addWidget(self.rd_p); r_dir.addWidget(self.rd_l); r_dir.addStretch(); l2.addLayout(r_dir)
        
        self.b1.clicked.connect(lambda: [self.rd_p.setChecked(True), self.trigger_refresh()])
        self.b2.clicked.connect(lambda: [self.rd_l.setChecked(True), self.trigger_refresh()])
        self.b4.clicked.connect(lambda: [self.rd_p.setChecked(True), self.trigger_refresh()])

        self.chk_cut = QCheckBox("显示裁剪辅助线"); self.chk_cut.setChecked(True); self.chk_cut.stateChanged.connect(self.trigger_refresh)
        l2.addWidget(self.chk_cut); rv.addWidget(c2)

        c3 = Card(); l3 = QVBoxLayout(c3)
        self.lbl_inf = QLabel("0 张发票"); self.lbl_tot = QLabel("¥ 0.00", styleSheet="font-size:20px; font-weight:bold; color:#007AFF")
        l3.addWidget(self.lbl_inf); l3.addWidget(self.lbl_tot)
        self.btn_xls = QPushButton(" 导出 Excel"); self.btn_xls.clicked.connect(self.xls); l3.addWidget(self.btn_xls); rv.addWidget(c3)

        self.btn_go = QPushButton(" 开始打印"); self.btn_go.setObjectName("PrimaryBtn"); self.btn_go.setMinimumHeight(50)
        self.btn_go.clicked.connect(self.run); rv.addWidget(self.btn_go); rv.addStretch()

        layout.addWidget(left); layout.addWidget(mid, 1); layout.addWidget(right)

    def change_theme(self, mode):
        self.theme_c = ThemeManager.apply(QApplication.instance(), mode)
        self.drag.upd(self.theme_c)
        self.btn_set.setIcon(Icons.get("settings", self.theme_c))
        self.btn_del.setIcon(Icons.get("trash", self.theme_c))
        self.btn_clr.setIcon(Icons.get("trash", "#d73a49"))
        self.btn_xls.setIcon(Icons.get("excel", self.theme_c))
        self.btn_go.setIcon(Icons.get("print", "white"))
        # 更新排版图标
        self.b1.setIcon(Icons.get("layout_1x1", self.theme_c))
        self.b2.setIcon(Icons.get("layout_1x2", self.theme_c))
        self.b4.setIcon(Icons.get("layout_2x2", self.theme_c))

    def trigger_refresh(self): self.preview_timer.start(200)

    def generate_realtime_preview(self):
        m="1x1"; m="1x2" if self.b2.isChecked() else m; m="2x2" if self.b4.isChecked() else m
        doc = PDFEngine.merge([x['p'] for x in self.data], m, self.cb_pap.currentText(), self.chk_cut.isChecked(), out_path=None)
        page_imgs = []
        if doc:
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                img = QImage.fromData(pix.tobytes("ppm"))
                page_imgs.append(img)
            doc.close()
        self.word_preview.show_pages(page_imgs)

    def add_files(self, fs):
        s=QSettings("MySoft","InvoiceMaster"); ak,sk=s.value("ak"),s.value("sk")
        for f in fs:
            d = {"p":f, "n":os.path.basename(f), "d":"", "a":0.0}
            self.list.addItem(QListWidgetItem(QIcon(InvoiceHelper.thumb(f)), d['n']))
            QApplication.processEvents()
            if f.endswith(".pdf"):
                try: 
                    t=fitz.open(f)[0].get_text()
                    a=re.search(r'(小写|¥|￥)\s*([0-9,]+\.\d{2})',t); dt=re.search(r'\d{4}年\d{1,2}月\d{1,2}日',t)
                    if a: d["a"]=float(a.group(2).replace(",",""))
                    if dt: d["d"]=dt.group(0)
                except: pass
            if d["a"]==0 and ak:
                r=InvoiceHelper.ocr(f,ak,sk); 
                if r: d["a"]=float(r.get("AmountInFiguers",0)); d["d"]=r.get("InvoiceDate","")
            self.list.item(self.list.count()-1).setText(f"{d['n']}\n{d['d']} | ¥{d['a']}")
            self.data.append(d)
        self.calc(); self.trigger_refresh()

    def calc(self): t=sum(x["a"] for x in self.data); self.lbl_inf.setText(f"{len(self.data)} 张发票"); self.lbl_tot.setText(f"¥ {t:,.2f}")
    def clear(self): self.list.clear(); self.data=[]; self.calc(); self.trigger_refresh()
    def keyPressEvent(self, e): 
        if e.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace): self.del_sel()
    def ctx_menu(self, p): 
        m=QMenu(); a=QAction("删除",self); a.triggered.connect(self.del_sel); m.addAction(a); m.exec(self.list.mapToGlobal(p))
    def del_sel(self):
        for r in sorted([self.list.row(i) for i in self.list.selectedItems()], reverse=True):
            self.list.takeItem(r); self.data.pop(r)
        self.calc(); self.trigger_refresh()
    def xls(self):
        if not self.data: return
        p, _ = QFileDialog.getSaveFileName(self, "Save", "report.xlsx", "Excel (*.xlsx)")
        if p: pd.DataFrame(self.data)[["d","n","a","p"]].rename(columns={"d":"日期","n":"文件名","a":"金额","p":"路径"}).to_excel(p, index=False); QMessageBox.information(self,"OK","Done")
    def run(self):
        if not self.data: return QMessageBox.warning(self,"Tips","请先添加发票")
        self.btn_go.setText("处理中..."); QApplication.processEvents()
        m="1x1"; m="1x2" if self.b2.isChecked() else m; m="2x2" if self.b4.isChecked() else m
        out = os.path.expanduser("~/Desktop/Print_Job.pdf")
        try:
            PDFEngine.merge([x["p"] for x in self.data], m, self.cb_pap.currentText(), self.chk_cut.isChecked(), out)
            copies = self.sp_cpy.value()
            if self.cb_pr.currentIndex() == 0: os.system(f"open '{out}'"); self.btn_go.setText(" 开始打印")
            else:
                p_name = self.cb_pr.currentText().replace("🖨️ ",""); self.btn_go.setText(f"发送至 {p_name}...")
                os.system(f"lp -d '{p_name}' -n {copies} '{out}'"); QMessageBox.information(self,"完成","已发送"); self.btn_go.setText(" 开始打印")
        except Exception as e: self.btn_go.setText("重试"); QMessageBox.critical(self,"Error",str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pix = QPixmap(400, 260); pix.fill(QColor("white")); p = QPainter(pix)
    p.setPen(QColor("#007AFF")); p.setFont(QFont("Arial", 28, QFont.Weight.Bold))
    p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "InvoiceMaster V17"); p.end()
    splash = QSplashScreen(pix); splash.show(); time.sleep(1)
    w = MainWindow(); w.show(); splash.finish(w)
    sys.exit(app.exec())