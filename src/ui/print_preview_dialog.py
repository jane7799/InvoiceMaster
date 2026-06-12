
"""
打印预览对话框
提供类似 WPS/FoxIt 的打印设置 & 预览界面
"""
import os
import logging
import fitz  # PyMuPDF

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                           QPushButton, QComboBox, QSpinBox, QCheckBox,
                           QRadioButton, QButtonGroup, QLineEdit, QFrame,
                           QWidget, QGraphicsDropShadowEffect, QScrollArea,
                           QMessageBox, QApplication, QSizePolicy)
from PyQt6.QtGui import QColor, QPixmap, QImage, QPageLayout
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtPrintSupport import QPrinter, QPrinterInfo, QPrintDialog

from src.utils.icons import Icons
from src.core.workers import PrintWorker

logger = logging.getLogger(__name__)


# ──────────────────────── 样式常量 ────────────────────────
_DIALOG_BG = "background-color: #F0F2F5;"
_HEADER_GRADIENT = """
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #7C3AED);
"""
_CARD_STYLE = """
    QFrame#Card {
        background-color: white;
        border-radius: 12px;
    }
"""
_LABEL_TITLE = "font-size: 13px; font-weight: 600; color: #1E293B;"
_LABEL_HINT = "font-size: 12px; color: #64748B;"
_COMBO_STYLE = """
    QComboBox {
        border: 1.5px solid #E2E8F0; border-radius: 8px;
        padding: 6px 10px; background: white;
        font-size: 13px; color: #334155;
        min-height: 28px;
    }
    QComboBox:hover  { border-color: #3B82F6; }
    QComboBox:focus  { border-color: #2563EB; }
    QComboBox::drop-down { border: none; width: 24px; }
    QComboBox::down-arrow { image: none; border: none; }
    QComboBox QAbstractItemView {
        border: 1px solid #E2E8F0; border-radius: 6px;
        background: white; selection-background-color: #EFF6FF;
        selection-color: #1E293B; padding: 4px;
    }
"""
_SPIN_STYLE = """
    QSpinBox {
        border: 1.5px solid #E2E8F0; border-radius: 8px;
        padding: 6px 10px; background: white;
        font-size: 13px; color: #334155;
        min-height: 28px;
    }
    QSpinBox:hover { border-color: #3B82F6; }
    QSpinBox:focus { border-color: #2563EB; }
"""
_LINE_EDIT_STYLE = """
    QLineEdit {
        border: 1.5px solid #E2E8F0; border-radius: 8px;
        padding: 6px 10px; background: white;
        font-size: 13px; color: #334155;
        min-height: 28px;
    }
    QLineEdit:hover { border-color: #3B82F6; }
    QLineEdit:focus { border-color: #2563EB; }
"""
_RADIO_STYLE = """
    QRadioButton { font-size: 13px; color: #334155; spacing: 6px; }
    QRadioButton::indicator { width: 16px; height: 16px; }
"""
_CHECK_STYLE = """
    QCheckBox { font-size: 13px; color: #334155; spacing: 6px; }
    QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px; }
"""
_BTN_PRIMARY = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3B82F6, stop:1 #2563EB);
        border: none; border-radius: 8px;
        padding: 10px 32px; color: white;
        font-size: 14px; font-weight: 600;
        min-height: 20px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #60A5FA, stop:1 #3B82F6);
    }
    QPushButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2563EB, stop:1 #1D4ED8);
    }
    QPushButton:disabled { background: #94A3B8; }
"""
_BTN_SECONDARY = """
    QPushButton {
        background-color: #F1F5F9; border: 1.5px solid #E2E8F0;
        border-radius: 8px; padding: 10px 24px;
        color: #475569; font-size: 14px; font-weight: 500;
        min-height: 20px;
    }
    QPushButton:hover { background-color: #E2E8F0; border-color: #CBD5E1; }
"""
_BTN_SMALL = """
    QPushButton {
        background-color: #F1F5F9; border: 1.5px solid #E2E8F0;
        border-radius: 6px; padding: 5px 12px;
        color: #475569; font-size: 12px; font-weight: 500;
    }
    QPushButton:hover { background-color: #E2E8F0; border-color: #CBD5E1; }
"""
_NAV_BTN_STYLE = """
    QPushButton {
        background-color: rgba(255,255,255,0.15); border: none;
        border-radius: 6px; padding: 4px 8px;
        color: #94A3B8; font-size: 13px; font-weight: 500;
        min-width: 28px; min-height: 28px;
    }
    QPushButton:hover { background-color: rgba(255,255,255,0.25); color: white; }
    QPushButton:disabled { color: rgba(255,255,255,0.15); }
"""
_PREVIEW_BG = "background-color: #3D4248; border-radius: 0 12px 12px 0;"
_SEPARATOR = """
    QFrame { background-color: #E2E8F0; }
"""


def _make_shadow(blur=20, alpha=30, dy=2):
    """创建卡片阴影"""
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(blur); s.setColor(QColor(0, 0, 0, alpha)); s.setOffset(0, dy)
    return s


class PrintPreviewDialog(QDialog):
    """打印预览对话框 — 类似 WPS / FoxIt 打印界面"""

    print_requested = pyqtSignal()  # 打印完成信号

    def __init__(self, pdf_path, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.setWindowTitle("打印预览")
        self.setModal(True)
        self.resize(920, 660)
        self.setMinimumSize(780, 520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setStyleSheet(f"QDialog {{ {_DIALOG_BG} }}")

        # 内部状态
        self._page_images = []   # list[QImage]  — 预渲染的页面缩略图
        self._total_pages = 0
        self._current_page = 0   # 0-indexed
        self._print_worker = None
        self._printer = QPrinter(QPrinter.PrinterMode.HighResolution)

        self._build_ui()
        self._load_pdf()

    # ──────────────────── 公共接口 ────────────────────
    def set_printer_name(self, name: str):
        """从主窗口预选打印机"""
        idx = self.cb_printer.findText(name)
        if idx >= 0:
            self.cb_printer.setCurrentIndex(idx)

    # ──────────────────── UI 构建 ────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        # ── 渐变标题栏 ──
        header = QWidget(); header.setFixedHeight(52)
        header.setStyleSheet(_HEADER_GRADIENT)
        h_lay = QHBoxLayout(header); h_lay.setContentsMargins(20, 0, 20, 0)
        title = QLabel("🖨️ 打印预览")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: white; background: transparent;")
        h_lay.addWidget(title); h_lay.addStretch()
        root.addWidget(header)

        # ── 主体（左设置 + 右预览）──
        body = QHBoxLayout(); body.setContentsMargins(16, 16, 16, 16); body.setSpacing(0)

        # 左侧设置面板
        left_card = QFrame(); left_card.setObjectName("Card"); left_card.setStyleSheet(_CARD_STYLE)
        left_card.setFixedWidth(340); left_card.setGraphicsEffect(_make_shadow())
        self._build_left_panel(left_card)
        body.addWidget(left_card)

        # 分割线
        sep = QFrame(); sep.setFixedWidth(1); sep.setStyleSheet(_SEPARATOR)
        body.addWidget(sep)

        # 右侧预览面板
        right_card = QFrame(); right_card.setObjectName("Card")
        right_card.setStyleSheet("QFrame#Card { background-color: #3D4248; border-radius: 0 12px 12px 0; }")
        right_card.setGraphicsEffect(_make_shadow(blur=24, alpha=40, dy=3))
        self._build_right_panel(right_card)
        body.addWidget(right_card, 1)

        root.addLayout(body, 1)

        # ── 底部按钮栏 ──
        footer = QHBoxLayout(); footer.setContentsMargins(20, 8, 20, 16); footer.setSpacing(12)
        footer.addStretch()

        self.btn_print = QPushButton(" 打印"); self.btn_print.setStyleSheet(_BTN_PRIMARY)
        self.btn_print.setIcon(Icons.get("print", "white")); self.btn_print.setIconSize(QSize(18, 18))
        self.btn_print.clicked.connect(self._on_print)
        footer.addWidget(self.btn_print)

        btn_close = QPushButton("关闭"); btn_close.setStyleSheet(_BTN_SECONDARY)
        btn_close.clicked.connect(self.reject)
        footer.addWidget(btn_close)
        root.addLayout(footer)

    # ── 左侧面板 ──
    def _build_left_panel(self, card):
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        inner = QWidget(); inner.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(inner); lay.setContentsMargins(20, 18, 20, 18); lay.setSpacing(14)

        # ① 打印机
        lay.addWidget(self._section_label("打印机"))
        printer_row = QHBoxLayout(); printer_row.setSpacing(8)
        self.cb_printer = QComboBox(); self.cb_printer.setStyleSheet(_COMBO_STYLE)
        for name in QPrinterInfo.availablePrinterNames():
            self.cb_printer.addItem(name)
        # 默认选中系统默认打印机
        default_name = QPrinterInfo.defaultPrinter().printerName()
        if default_name:
            idx = self.cb_printer.findText(default_name)
            if idx >= 0: self.cb_printer.setCurrentIndex(idx)
        printer_row.addWidget(self.cb_printer, 1)
        btn_prop = QPushButton("属性"); btn_prop.setStyleSheet(_BTN_SMALL)
        btn_prop.clicked.connect(self._open_printer_properties)
        printer_row.addWidget(btn_prop)
        lay.addLayout(printer_row)

        lay.addWidget(self._thin_separator())

        # ② 打印份数
        lay.addWidget(self._section_label("打印份数"))
        copies_row = QHBoxLayout(); copies_row.setSpacing(8)
        self.sp_copies = QSpinBox(); self.sp_copies.setRange(1, 99); self.sp_copies.setValue(1)
        self.sp_copies.setStyleSheet(_SPIN_STYLE); self.sp_copies.setFixedWidth(90)
        copies_row.addWidget(self.sp_copies); copies_row.addStretch()
        lay.addLayout(copies_row)

        lay.addWidget(self._thin_separator())

        # ③ 颜色
        lay.addWidget(self._section_label("颜色"))
        self.chk_color = QCheckBox("彩色打印"); self.chk_color.setChecked(True)
        self.chk_color.setStyleSheet(_CHECK_STYLE)
        lay.addWidget(self.chk_color)

        lay.addWidget(self._thin_separator())

        # ④ 页面范围
        lay.addWidget(self._section_label("页面范围"))
        self.bg_range = QButtonGroup(self)
        self.rd_all = QRadioButton("所有页面"); self.rd_all.setChecked(True); self.rd_all.setStyleSheet(_RADIO_STYLE)
        self.rd_cur = QRadioButton("当前页面"); self.rd_cur.setStyleSheet(_RADIO_STYLE)
        self.rd_sel = QRadioButton("页码选择"); self.rd_sel.setStyleSheet(_RADIO_STYLE)
        self.bg_range.addButton(self.rd_all, 0); self.bg_range.addButton(self.rd_cur, 1); self.bg_range.addButton(self.rd_sel, 2)
        lay.addWidget(self.rd_all); lay.addWidget(self.rd_cur)
        sel_row = QHBoxLayout(); sel_row.setSpacing(8)
        sel_row.addWidget(self.rd_sel)
        self.le_pages = QLineEdit(); self.le_pages.setPlaceholderText("例: 1-3,5")
        self.le_pages.setStyleSheet(_LINE_EDIT_STYLE); self.le_pages.setFixedWidth(130)
        self.le_pages.setEnabled(False)
        sel_row.addWidget(self.le_pages); sel_row.addStretch()
        lay.addLayout(sel_row)
        self.bg_range.idToggled.connect(lambda id_, checked: self.le_pages.setEnabled(id_ == 2 and checked))

        lay.addWidget(self._thin_separator())

        # ⑤ 纸张方向
        lay.addWidget(self._section_label("纸张方向"))
        orient_row = QHBoxLayout(); orient_row.setSpacing(16)
        self.bg_orient = QButtonGroup(self)
        self.rd_portrait = QRadioButton("纵向"); self.rd_portrait.setChecked(True); self.rd_portrait.setStyleSheet(_RADIO_STYLE)
        self.rd_landscape = QRadioButton("横向"); self.rd_landscape.setStyleSheet(_RADIO_STYLE)
        self.bg_orient.addButton(self.rd_portrait, 0); self.bg_orient.addButton(self.rd_landscape, 1)
        orient_row.addWidget(self.rd_portrait); orient_row.addWidget(self.rd_landscape); orient_row.addStretch()
        lay.addLayout(orient_row)

        lay.addWidget(self._thin_separator())

        # ⑥ 打印方式
        lay.addWidget(self._section_label("打印方式"))
        self.bg_mode = QButtonGroup(self)
        self.rd_fit = QRadioButton("适合打印边距"); self.rd_fit.setChecked(True); self.rd_fit.setStyleSheet(_RADIO_STYLE)
        self.rd_actual = QRadioButton("实际大小"); self.rd_actual.setStyleSheet(_RADIO_STYLE)
        self.rd_custom = QRadioButton("自定义比例"); self.rd_custom.setStyleSheet(_RADIO_STYLE)
        self.bg_mode.addButton(self.rd_fit, 0); self.bg_mode.addButton(self.rd_actual, 1); self.bg_mode.addButton(self.rd_custom, 2)
        lay.addWidget(self.rd_fit); lay.addWidget(self.rd_actual)
        custom_row = QHBoxLayout(); custom_row.setSpacing(8)
        custom_row.addWidget(self.rd_custom)
        self.sp_scale = QSpinBox(); self.sp_scale.setRange(10, 400); self.sp_scale.setValue(100)
        self.sp_scale.setSuffix(" %"); self.sp_scale.setStyleSheet(_SPIN_STYLE); self.sp_scale.setFixedWidth(100)
        self.sp_scale.setEnabled(False)
        custom_row.addWidget(self.sp_scale); custom_row.addStretch()
        lay.addLayout(custom_row)
        self.bg_mode.idToggled.connect(lambda id_, checked: self.sp_scale.setEnabled(id_ == 2 and checked))

        lay.addWidget(self._thin_separator())

        # ⑦ 双面打印
        self.chk_duplex = QCheckBox("双面打印"); self.chk_duplex.setStyleSheet(_CHECK_STYLE)
        lay.addWidget(self.chk_duplex)

        lay.addStretch()
        scroll.setWidget(inner)
        card_lay = QVBoxLayout(card); card_lay.setContentsMargins(0, 0, 0, 0)
        card_lay.addWidget(scroll)

    # ── 右侧面板 ──
    def _build_right_panel(self, card):
        lay = QVBoxLayout(card); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)

        # 预览内容选择栏
        top_bar = QHBoxLayout(); top_bar.setContentsMargins(14, 10, 14, 6); top_bar.setSpacing(8)
        lbl_pv = QLabel("预览"); lbl_pv.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 12px; font-weight: 600; background:transparent;")
        top_bar.addWidget(lbl_pv)
        self.cb_content = QComboBox(); self.cb_content.addItem("仅文档")
        self.cb_content.setFixedWidth(110)
        self.cb_content.setStyleSheet("""
            QComboBox {
                border: 1px solid rgba(255,255,255,0.15); border-radius: 6px;
                padding: 4px 8px; background: rgba(255,255,255,0.1);
                color: rgba(255,255,255,0.8); font-size: 12px; min-height: 22px;
            }
            QComboBox::drop-down { border:none; width:20px; }
            QComboBox::down-arrow { image:none; }
        """)
        top_bar.addWidget(self.cb_content); top_bar.addStretch()
        lay.addLayout(top_bar)

        # 预览图像区域
        self.scroll_preview = QScrollArea()
        self.scroll_preview.setWidgetResizable(True); self.scroll_preview.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_preview.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        self.scroll_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background: transparent;")
        self.scroll_preview.setWidget(self.preview_label)
        lay.addWidget(self.scroll_preview, 1)

        # 翻页控制条
        nav = QHBoxLayout(); nav.setContentsMargins(14, 6, 14, 10); nav.setSpacing(6)
        nav.addStretch()

        self.btn_first = QPushButton("⏮"); self.btn_first.setStyleSheet(_NAV_BTN_STYLE); self.btn_first.setToolTip("第一页")
        self.btn_first.clicked.connect(lambda: self._go_page(0))
        nav.addWidget(self.btn_first)

        self.btn_prev = QPushButton(); self.btn_prev.setIcon(Icons.get("prev", "#94A3B8"))
        self.btn_prev.setStyleSheet(_NAV_BTN_STYLE); self.btn_prev.setToolTip("上一页")
        self.btn_prev.clicked.connect(lambda: self._go_page(self._current_page - 1))
        nav.addWidget(self.btn_prev)

        self.le_page_num = QLineEdit("1"); self.le_page_num.setFixedWidth(42)
        self.le_page_num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.le_page_num.setStyleSheet("""
            QLineEdit {
                border: 1px solid rgba(255,255,255,0.2); border-radius: 4px;
                background: rgba(255,255,255,0.1); color: white;
                font-size: 13px; padding: 3px;
            }
        """)
        self.le_page_num.returnPressed.connect(self._on_page_input)
        nav.addWidget(self.le_page_num)

        self.lbl_total = QLabel("/ 0")
        self.lbl_total.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 13px; background:transparent;")
        nav.addWidget(self.lbl_total)

        self.btn_next = QPushButton(); self.btn_next.setIcon(Icons.get("next", "#94A3B8"))
        self.btn_next.setStyleSheet(_NAV_BTN_STYLE); self.btn_next.setToolTip("下一页")
        self.btn_next.clicked.connect(lambda: self._go_page(self._current_page + 1))
        nav.addWidget(self.btn_next)

        self.btn_last = QPushButton("⏭"); self.btn_last.setStyleSheet(_NAV_BTN_STYLE); self.btn_last.setToolTip("最后一页")
        self.btn_last.clicked.connect(lambda: self._go_page(self._total_pages - 1))
        nav.addWidget(self.btn_last)

        nav.addStretch()
        lay.addLayout(nav)

    # ──────────────────── PDF 加载 & 渲染 ────────────────────
    def _load_pdf(self):
        """用 fitz 打开 PDF，渲染所有页面为 QImage"""
        if not os.path.exists(self.pdf_path):
            logger.error(f"PDF 文件不存在: {self.pdf_path}")
            return
        try:
            doc = fitz.open(self.pdf_path)
            self._total_pages = len(doc)
            self._page_images = []
            # 以 2x 缩放渲染缩略图（平衡清晰度与内存）
            mat = fitz.Matrix(2.0, 2.0)
            for page in doc:
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                # 深拷贝，避免 fitz 内存释放后悬挂指针
                self._page_images.append(img.copy())
            doc.close()
        except Exception as e:
            logger.error(f"加载 PDF 失败: {e}")
            self._total_pages = 0
            self._page_images = []

        self.lbl_total.setText(f"/ {self._total_pages}")
        if self._total_pages > 0:
            self._go_page(0)
        else:
            self.preview_label.setText("无法加载预览")
            self.preview_label.setStyleSheet("color:rgba(255,255,255,0.4);font-size:14px;background:transparent;")

    def _go_page(self, idx):
        """跳转到指定页"""
        if self._total_pages == 0:
            return
        idx = max(0, min(idx, self._total_pages - 1))
        self._current_page = idx
        self.le_page_num.setText(str(idx + 1))
        self._render_current_page()
        # 更新按钮状态
        self.btn_first.setEnabled(idx > 0); self.btn_prev.setEnabled(idx > 0)
        self.btn_next.setEnabled(idx < self._total_pages - 1); self.btn_last.setEnabled(idx < self._total_pages - 1)

    def _render_current_page(self):
        """渲染当前页到预览区域"""
        if not self._page_images:
            return
        img = self._page_images[self._current_page]
        pix = QPixmap.fromImage(img)
        # 按预览区域宽度自适应缩放
        view_w = self.scroll_preview.viewport().width() - 40
        view_h = self.scroll_preview.viewport().height() - 40
        if view_w < 200: view_w = 200
        if view_h < 200: view_h = 200
        scaled = pix.scaled(view_w, view_h, Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation)
        self.preview_label.setPixmap(scaled)
        # 阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30); shadow.setColor(QColor(0, 0, 0, 120)); shadow.setOffset(0, 6)
        self.preview_label.setGraphicsEffect(shadow)

    def _on_page_input(self):
        """手动输入页码"""
        try:
            num = int(self.le_page_num.text())
            self._go_page(num - 1)
        except ValueError:
            self.le_page_num.setText(str(self._current_page + 1))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._page_images:
            self._render_current_page()

    # ──────────────────── 打印机属性 ────────────────────
    def _open_printer_properties(self):
        """打开系统打印机属性对话框"""
        printer = QPrinter()
        name = self.cb_printer.currentText()
        if name:
            printer.setPrinterName(name)
        dlg = QPrintDialog(printer, self)
        dlg.exec()

    # ──────────────────── 解析页面范围 ────────────────────
    def _parse_page_range(self):
        """
        解析用户选择的页面范围，返回 0-indexed 页码列表。
        None 表示打印全部页面（由 PrintWorker 处理）。
        """
        checked_id = self.bg_range.checkedId()
        if checked_id == 0:
            # 所有页面
            return None
        elif checked_id == 1:
            # 当前页面
            return [self._current_page]
        else:
            # 页码选择
            text = self.le_pages.text().strip()
            if not text:
                return None
            pages = set()
            for part in text.split(","):
                part = part.strip()
                if "-" in part:
                    try:
                        a, b = part.split("-", 1)
                        for p in range(int(a), int(b) + 1):
                            if 1 <= p <= self._total_pages:
                                pages.add(p - 1)
                    except ValueError:
                        pass
                else:
                    try:
                        p = int(part)
                        if 1 <= p <= self._total_pages:
                            pages.add(p - 1)
                    except ValueError:
                        pass
            return sorted(pages) if pages else None

    # ──────────────────── 执行打印 ────────────────────
    def _on_print(self):
        """收集设置并执行打印"""
        p_name = self.cb_printer.currentText()
        if not p_name:
            QMessageBox.warning(self, "提示", "请选择打印机")
            return

        self.btn_print.setEnabled(False)
        self.btn_print.setText(" 准备打印...")
        QApplication.processEvents()

        # 配置 QPrinter
        self._printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        self._printer.setPrinterName(p_name)

        # 份数
        copies = self.sp_copies.value()

        # 颜色模式
        if self.chk_color.isChecked():
            self._printer.setColorMode(QPrinter.ColorMode.Color)
        else:
            self._printer.setColorMode(QPrinter.ColorMode.GrayScale)

        # 方向
        force_rotate = self.rd_landscape.isChecked()
        if force_rotate:
            self._printer.setPageOrientation(QPageLayout.Orientation.Landscape)
        else:
            self._printer.setPageOrientation(QPageLayout.Orientation.Portrait)

        # 双面打印
        if self.chk_duplex.isChecked():
            self._printer.setDuplex(QPrinter.DuplexMode.DuplexLongSide)
        else:
            self._printer.setDuplex(QPrinter.DuplexMode.DuplexNone)

        # 页面范围 — 如果选择了特定页面，需要生成子 PDF
        page_range = self._parse_page_range()
        pdf_to_print = self.pdf_path

        if page_range is not None and len(page_range) < self._total_pages:
            # 创建仅包含选定页面的临时 PDF
            try:
                import tempfile
                tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf", prefix="print_subset_")
                os.close(tmp_fd)
                src = fitz.open(self.pdf_path)
                dst = fitz.open()
                for pg_idx in page_range:
                    dst.insert_pdf(src, from_page=pg_idx, to_page=pg_idx)
                dst.save(tmp_path)
                dst.close(); src.close()
                pdf_to_print = tmp_path
            except Exception as e:
                logger.error(f"创建子页面 PDF 失败: {e}")
                QMessageBox.critical(self, "错误", f"准备打印页面失败: {e}")
                self.btn_print.setEnabled(True); self.btn_print.setText(" 打印")
                return

        # 使用 PrintWorker 异步打印
        self._print_worker = PrintWorker(pdf_to_print, self._printer, copies, force_rotate, self)
        self._print_worker.progress.connect(self._on_print_progress)
        self._print_worker.finished.connect(self._on_print_finished)
        self._print_worker.start()

    def _on_print_progress(self, current, total):
        self.btn_print.setText(f" 打印中 ({current}/{total})...")
        QApplication.processEvents()

    def _on_print_finished(self, success, msg):
        self._print_worker = None
        self.btn_print.setEnabled(True)
        self.btn_print.setText(" 打印")
        if success:
            QMessageBox.information(self, "完成", "打印任务已发送至打印机")
            self.print_requested.emit()
            self.accept()
        else:
            QMessageBox.critical(self, "打印失败", msg)

    # ──────────────────── 辅助 ────────────────────
    @staticmethod
    def _section_label(text):
        lbl = QLabel(text); lbl.setStyleSheet(_LABEL_TITLE)
        return lbl

    @staticmethod
    def _thin_separator():
        sep = QFrame(); sep.setFixedHeight(1)
        sep.setStyleSheet("QFrame{background-color:#F1F5F9;}")
        return sep
