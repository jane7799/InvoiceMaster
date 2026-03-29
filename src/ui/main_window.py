
import os
import sys
import gc
import logging
import platform
import fitz  # PyMuPDF
import pandas as pd
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QListWidget, QListWidgetItem, 
                           QStackedWidget, QComboBox, QCheckBox, QRadioButton,
                           QButtonGroup, QToolButton, QFileDialog, QMessageBox,
                           QInputDialog, QSpinBox, QApplication, QAbstractItemView,
                           QMenu, QFrame)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon, QImage, QAction, QTransform
from PyQt6.QtPrintSupport import QPrinter, QPrinterInfo, QPrintDialog
from PyQt6.QtCore import QSettings

from src.core.invoice_helper import InvoiceHelper
from src.core.pdf_engine import PDFEngine
from src.core.workers import OcrWorker, PdfWorker, PrintWorker
# 激活功能已移除
from src.core.database import get_db
from src.themes.theme_manager import ThemeManager
from src.utils.log_manager import LogManager
from src.utils.icons import Icons
from src.utils.constants import APP_NAME, APP_VERSION, APP_AUTHOR_CN
from src.utils.utils import resource_path
from src.utils.config import UI_CONFIG

from src.ui.dialogs import ProgressDialog, AboutDialog
from src.ui.settings_dialog import SettingsDlg
from src.ui.statistics_dialog import StatisticsDialog
from src.ui.widgets import Card, GlassCard, DragArea, InvoiceItemWidget
from src.ui.preview import AdvancedPreviewArea, SingleDocViewer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.resize(1350, 850); self.data = []; self.theme_c = "#555"
        self.temp_files = [] 
        self.preview_timer = QTimer(); self.preview_timer.setSingleShot(True); self.preview_timer.timeout.connect(self.generate_realtime_preview)
        self.current_printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        self.right_panel = None; self.settings_card = None
        # 激活功能已移除
        
        # 异步工作线程引用
        self.ocr_worker = None
        self.pdf_worker = None
        self.print_worker = None
        self.progress_dialog = None
        
        self.init_ui()
        ThemeManager.apply(QApplication.instance())
        self.change_theme("Light")

    def closeEvent(self, event):
        """应用关闭时清理资源"""
        import logging
        logger = logging.getLogger(__name__)
        
        # 清理临时文件
        for f in self.temp_files:
            try: os.remove(f)
            except: pass
        
        # [V3.6] 清除数据库缓存，避免上一次数据带入下一次
        try:
            from src.core.database import get_db
            deleted = get_db().clear_all()
            logger.info(f"关闭时清除数据库缓存: {deleted} 条记录")
        except Exception as e:
            logger.warning(f"清除数据库缓存失败: {e}")
        
        super().closeEvent(event)

    def init_ui(self):
        main = QWidget(); self.setCentralWidget(main)
        layout = QHBoxLayout(main); layout.setContentsMargins(12, 12, 12, 12); layout.setSpacing(12)

        # ── 左侧面板 ──
        left = QWidget(); left.setFixedWidth(290); lv = QVBoxLayout(left); lv.setContentsMargins(0,0,0,0); lv.setSpacing(10)
        
        # 拖放区域
        self.drag = DragArea(); self.drag.dropped.connect(self.add_files)
        lv.addWidget(self.drag)
        
        # 发票清单标题行
        list_header = QHBoxLayout(); list_header.setContentsMargins(2, 4, 2, 0)
        list_title = QLabel("发票清单"); list_title.setObjectName("SectionTitle")
        self.list_count_badge = QLabel("0"); self.list_count_badge.setFixedSize(24, 18)
        self.list_count_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.list_count_badge.setStyleSheet("background: #E2E8F0; color: #64748B; border-radius: 9px; font-size: 11px; font-weight: 600;")
        list_hint = QLabel("双击修正金额"); list_hint.setStyleSheet("color: #94A3B8; font-size: 11px;")
        
        self.btn_del = QPushButton("清空"); self.btn_del.setFixedHeight(24)
        self.btn_del.setIcon(Icons.get("trash", "#94A3B8")); self.btn_del.setIconSize(QSize(12, 12))
        self.btn_del.setStyleSheet("""
            QPushButton {
                background: transparent; border: none; border-radius: 4px;
                color: #94A3B8; font-size: 11px; padding: 2px 6px;
            }
            QPushButton:hover {
                background: #FEE2E2; color: #DC2626;
            }
        """)
        self.btn_del.clicked.connect(self.clear)
        
        list_header.addWidget(list_title); list_header.addWidget(self.list_count_badge)
        list_header.addStretch(); list_header.addWidget(list_hint); list_header.addWidget(self.btn_del)
        lv.addLayout(list_header)
        
        self.list = QListWidget(); self.list.setIconSize(QSize(40,50)); self.list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu); self.list.customContextMenuRequested.connect(self.ctx_menu)
        self.list.itemDoubleClicked.connect(self.edit_item); self.list.itemClicked.connect(self.show_single_doc)
        
        lv.addWidget(self.list)
        
        # 底部版权
        footer_lbl = QLabel(APP_AUTHOR_CN, alignment=Qt.AlignmentFlag.AlignCenter)
        footer_lbl.setStyleSheet("color: #CBD5E1; font-size: 11px; padding: 4px 0;")
        lv.addWidget(footer_lbl)

        # ── 中间预览区 ──
        mid = QWidget(); mv = QVBoxLayout(mid); mv.setContentsMargins(0,0,0,0); mv.setSpacing(0)
        self.stack = QStackedWidget()
        self.word_preview = AdvancedPreviewArea() 
        self.single_viewer = SingleDocViewer() 
        self.stack.addWidget(self.word_preview); self.stack.addWidget(self.single_viewer)
        mv.addWidget(self.stack)

        # ── 右侧面板 ──
        self.right_panel = QWidget(); self.right_panel.setFixedWidth(330)
        rv = QVBoxLayout(self.right_panel); rv.setContentsMargins(0,0,0,0); rv.setSpacing(10)
        
        # 打印设置卡片
        self.settings_card = Card() 
        self.settings_layout = QVBoxLayout(self.settings_card)
        self.settings_layout.setSpacing(14); self.settings_layout.setContentsMargins(20,18,20,18)
        
        # 打印设置区块标题
        print_section_title = QLabel("打印设置"); print_section_title.setObjectName("SectionTitle")
        self.settings_layout.addWidget(print_section_title)
        
        r_pr = QHBoxLayout(); self.cb_pr = QComboBox(); self.cb_pr.addItem("🖥️ 默认打印机/PDF")
        if platform.system() in ["Windows", "Linux"]: 
            for p in QPrinterInfo.availablePrinterNames(): self.cb_pr.addItem(f"🖨️ {p}")
        self.cb_pr.currentIndexChanged.connect(self.on_printer_changed)
        
        self.btn_prop = QPushButton(); self.btn_prop.setObjectName("PropBtn"); self.btn_prop.setFixedSize(34, 34)
        self.btn_prop.setIcon(Icons.get("settings", "#94A3B8")); self.btn_prop.setIconSize(QSize(16, 16))
        self.btn_prop.setToolTip("打印机属性")
        self.btn_prop.clicked.connect(self.open_printer_props)
        self.btn_prop.setEnabled(False)
        r_pr.addWidget(self.cb_pr, 1); r_pr.addWidget(self.btn_prop); self.settings_layout.addLayout(r_pr)

        r_cp = QHBoxLayout(); r_cp.setSpacing(10)
        self.sp_cpy = QSpinBox(); self.sp_cpy.setRange(1,99); self.sp_cpy.setSuffix(" 份")
        self.cb_pap = QComboBox(); self.cb_pap.addItems(["A4", "A5", "B5"]); self.cb_pap.currentTextChanged.connect(self.show_layout_preview)
        lbl_copies = QLabel("份数"); lbl_copies.setStyleSheet("color: #64748B; font-size: 12px;")
        lbl_paper = QLabel("纸张"); lbl_paper.setStyleSheet("color: #64748B; font-size: 12px;")
        r_cp.addWidget(lbl_copies); r_cp.addWidget(self.sp_cpy); r_cp.addSpacing(5)
        r_cp.addWidget(lbl_paper); r_cp.addWidget(self.cb_pap); self.settings_layout.addLayout(r_cp)
        
        lbl_layout_mode = QLabel("排版模式"); lbl_layout_mode.setStyleSheet("color: #64748B; font-size: 12px; margin-top: 2px;")
        self.settings_layout.addWidget(lbl_layout_mode)
        rm = QHBoxLayout(); rm.setSpacing(8)
        self.b1 = QToolButton(); self.b1.setObjectName("LayoutCard"); self.b1.setFixedSize(85, 85); self.b1.setIconSize(QSize(72,72))
        self.b2 = QToolButton(); self.b2.setObjectName("LayoutCard"); self.b2.setFixedSize(85, 85); self.b2.setIconSize(QSize(72,72))
        self.b4 = QToolButton(); self.b4.setObjectName("LayoutCard"); self.b4.setFixedSize(85, 85); self.b4.setIconSize(QSize(72,72))
        self.b1.setCheckable(True); self.b2.setCheckable(True); self.b4.setCheckable(True)
        grp=QButtonGroup(self); grp.addButton(self.b1); grp.addButton(self.b2); grp.addButton(self.b4); self.b1.setChecked(True)
        grp.buttonClicked.connect(self.show_layout_preview)
        rm.addWidget(self.b1); rm.addWidget(self.b2); rm.addWidget(self.b4); rm.addStretch()
        self.settings_layout.addLayout(rm)

        r_dir = QHBoxLayout()
        self.rd_p = QRadioButton("纵向"); self.rd_l = QRadioButton("横向"); self.rd_l.setChecked(True)
        self.rd_p.toggled.connect(self.update_layout_icons); self.rd_l.toggled.connect(self.update_layout_icons)
        lbl_orient = QLabel("方向"); lbl_orient.setStyleSheet("color: #64748B; font-size: 12px;")
        r_dir.addWidget(lbl_orient); r_dir.addWidget(self.rd_p); r_dir.addWidget(self.rd_l); r_dir.addStretch()
        self.settings_layout.addLayout(r_dir)
        
        r_opt = QHBoxLayout()
        self.chk_cut = QCheckBox("裁剪辅助线"); self.chk_cut.setChecked(True); self.chk_cut.stateChanged.connect(self.show_layout_preview)
        self.chk_rotate = QCheckBox("强力纠偏"); self.chk_rotate.setToolTip("强制旋转90度打印，解决部分打印机方向错误问题")
        r_opt.addWidget(self.chk_cut); r_opt.addSpacing(10); r_opt.addWidget(self.chk_rotate); r_opt.addStretch()
        self.settings_layout.addLayout(r_opt)
        
        rv.addWidget(self.settings_card)

        # ── 统计卡片 ──
        stats_card = Card()
        stats_layout = QVBoxLayout(stats_card); stats_layout.setSpacing(10); stats_layout.setContentsMargins(20, 16, 20, 16)
        
        stats_title = QLabel("汇总"); stats_title.setObjectName("SectionTitle")
        stats_layout.addWidget(stats_title)
        
        # 统计数据网格
        stats_grid = QHBoxLayout(); stats_grid.setSpacing(0)
        
        # 发票数量
        count_col = QVBoxLayout(); count_col.setSpacing(2)
        self.lbl_inf = QLabel("0"); self.lbl_inf.setObjectName("StatsValue"); self.lbl_inf.setStyleSheet("font-size: 24px; font-weight: 700; color: #3B82F6;")
        lbl_count_label = QLabel("张发票"); lbl_count_label.setObjectName("StatsLabel")
        count_col.addWidget(self.lbl_inf); count_col.addWidget(lbl_count_label)
        stats_grid.addLayout(count_col)
        
        # 分隔线
        divider = QFrame(); divider.setFixedWidth(1); divider.setStyleSheet("background: #E2E8F0; margin: 4px 16px;")
        stats_grid.addWidget(divider)
        
        # 总金额
        amount_col = QVBoxLayout(); amount_col.setSpacing(2)
        self.lbl_tot = QLabel("¥0.00"); self.lbl_tot.setObjectName("StatsValue"); self.lbl_tot.setStyleSheet("font-size: 24px; font-weight: 700; color: #10B981;")
        lbl_amount_label = QLabel("合计金额"); lbl_amount_label.setObjectName("StatsLabel")
        amount_col.addWidget(self.lbl_tot); amount_col.addWidget(lbl_amount_label)
        stats_grid.addLayout(amount_col)
        
        stats_layout.addLayout(stats_grid)
        
        # 导出按钮
        self.btn_xls = QPushButton(" 导出 Excel"); self.btn_xls.setObjectName("ActionBtn")
        self.btn_xls.setIcon(Icons.get("excel", "#475569")); self.btn_xls.setFixedHeight(38)
        self.btn_xls.clicked.connect(self.xls)
        stats_layout.addWidget(self.btn_xls)
        rv.addWidget(stats_card)

        # ── 打印按钮 ──
        self.btn_go = QPushButton(" 开始打印"); self.btn_go.setObjectName("PrimaryBtn")
        self.btn_go.setIcon(Icons.get("print", "white")); self.btn_go.setMinimumHeight(50)
        self.btn_go.clicked.connect(self.run); rv.addWidget(self.btn_go)
        
        rv.addStretch()
        
        # ── 底部功能按钮 ──
        bottom_btns = QHBoxLayout(); bottom_btns.setSpacing(6)
        self.btn_set = QPushButton(" 设置"); self.btn_set.setObjectName("ActionBtn"); self.btn_set.setFixedHeight(34)
        self.btn_set.clicked.connect(lambda: SettingsDlg(self).exec())
        
        self.btn_stats = QPushButton(" 统计"); self.btn_stats.setObjectName("ActionBtn"); self.btn_stats.setFixedHeight(34)
        self.btn_stats.clicked.connect(lambda: StatisticsDialog(self, self.data).exec())
        
        btn_about = QPushButton(" 关于"); btn_about.setObjectName("ActionBtn"); btn_about.setFixedHeight(34)
        btn_about.clicked.connect(lambda: AboutDialog(self).exec())
        
        bottom_btns.addWidget(self.btn_set); bottom_btns.addWidget(self.btn_stats); bottom_btns.addWidget(btn_about)
        rv.addLayout(bottom_btns)

        layout.addWidget(left); layout.addWidget(mid, 1); layout.addWidget(self.right_panel)
        self.drag.upd("#555")

    def change_theme(self, mode):
        self.theme_c = ThemeManager.apply(QApplication.instance(), mode)
        self.drag.upd(self.theme_c)
        self.btn_set.setIcon(Icons.get("settings", self.theme_c))
        self.btn_del.setIcon(Icons.get("trash", "#DC2626")) 
        self.btn_xls.setIcon(Icons.get("excel", self.theme_c))
        self.btn_go.setIcon(Icons.get("print", "white"))
        self.btn_stats.setIcon(Icons.get("monitor", self.theme_c))
        self.update_layout_icons()

    def update_layout_icons(self):
        if not hasattr(self, 'rd_l') or not self.rd_l: return
        try: is_l = self.rd_l.isChecked()
        except RuntimeError: return 
        
        icon_1 = "icon_1x1_l.png" if is_l else "icon_1x1_p.png"
        if os.path.exists(resource_path(icon_1)): self.b1.setIcon(QIcon(resource_path(icon_1)))
        else: self.b1.setIcon(Icons.get("layout_1x1_card", self.theme_c))
        icon_2 = "icon_1x2_l.png" if is_l else "icon_1x2_p.png"
        if os.path.exists(resource_path(icon_2)): self.b2.setIcon(QIcon(resource_path(icon_2)))
        else: self.b2.setIcon(Icons.get("layout_1x2_card_h" if is_l else "layout_1x2_card_v", self.theme_c))
        icon_4 = "icon_2x2_l.png" if is_l else "icon_2x2_p.png"
        if os.path.exists(resource_path(icon_4)): self.b4.setIcon(QIcon(resource_path(icon_4)))
        else: self.b4.setIcon(Icons.get("layout_2x2_card", self.theme_c))
        btn_size = QSize(90, 65) if is_l else QSize(65, 90)
        icon_size = QSize(86, 61) if is_l else QSize(61, 86)
        for btn in [self.b1, self.b2, self.b4]:
            btn.setFixedSize(btn_size)
            btn.setIconSize(icon_size)
        self.show_layout_preview()
        
        # 自动清理可能产生的错误空数据（之前版本的bug）
        get_db().delete_invoice("")

    def _save_d_to_db(self, d):
        """辅助方法：将UI数据字典转换为数据库格式并保存"""
        # 基础数据来自 ext (OCR/解析结果)
        info = d.get("ext", {}).copy()
        
        # 强制覆盖核心字段（以UI显示的为准，支持用户手动修改）
        info["file_path"] = d.get("p")
        info["file_name"] = d.get("n")
        info["amount"] = d.get("a", 0.0)
        info["date"] = d.get("d", "")
        
        # 保存到数据库
        get_db().save_invoice(info)

    def delete_specific_item(self, item):
        row = self.list.row(item); self.list.takeItem(row); 
        d = self.data.pop(row)
        get_db().delete_invoice(d['p'])
        self.calc(); self.show_layout_preview()
    
    def show_single_doc(self, item):
        row = self.list.row(item)
        if row < len(self.data):
            f = self.data[row]['p']
            o = "H" if self.rd_l.isChecked() else "V"
            paper = self.cb_pap.currentText().replace("纸张: ", "") if "纸张: " in self.cb_pap.currentText() else self.cb_pap.currentText()
            doc = PDFEngine.merge([f], "1x1", paper, o, self.chk_cut.isChecked(), out_path=None)
            if doc:
                # 使用平台自适应的渲染分辨率
                scale = UI_CONFIG.get("preview_render_scale", 4.0)
                # 【V5.1】alpha=True + png: 确保发票章等透明图层在预览中正确渲染
                pix = doc[0].get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=True, annots=True)
                img = QImage.fromData(pix.tobytes("png"))
                
                # [V3.4.0] 单张预览也需要反向旋转修复 (与排版预览逻辑保持一致)
                if o == "H":
                    transform = QTransform()
                    transform.rotate(-90) # 修正: 逆时针90度
                    img = img.transformed(transform)
                    
                self.single_viewer.set_image(img) 
                doc.close() 
            self.stack.setCurrentIndex(1)

    def show_layout_preview(self): self.stack.setCurrentIndex(0); self.trigger_refresh()
    def edit_item(self, item):
        row = self.list.row(item)
        old_val = self.data[row].get('a', 0)
        val, ok = QInputDialog.getDouble(self, "修正金额", "请输入正确金额:", old_val, 0.00, 1000000, 2)
        if ok:
            self.data[row]['a'] = val
            self.data[row]['manually_edited'] = True
            self._save_d_to_db(self.data[row])
            widget = self.list.itemWidget(item)
            if widget:
                widget.update_display(self.data[row])
            self.calc()
    
    def on_printer_changed(self, idx):
        if idx == 0:
            self.btn_prop.setEnabled(False)
            self.btn_go.setText(" 预览 / 生成PDF")
        else:
            self.btn_prop.setEnabled(True)
            p_name = self.cb_pr.currentText().replace("🖨️ ", "")
            self.current_printer = QPrinter(QPrinterInfo.printerInfo(p_name), QPrinter.PrinterMode.HighResolution)
            self.btn_go.setText(f" 打印到: {p_name[:8]}...")

    def open_printer_props(self):
        dlg = QPrintDialog(self.current_printer, self)
        if dlg.exec() == QDialog.DialogCode.Accepted: pass 

    def trigger_refresh(self): self.preview_timer.start(200)
    def generate_realtime_preview(self):
        m="1x1"; m="1x2" if self.b2.isChecked() else m; m="2x2" if self.b4.isChecked() else m
        o="H" if self.rd_l.isChecked() else "V"; 
        
        rotate_preview = (o == "H")

        if hasattr(self, 'current_doc') and self.current_doc: self.current_doc.close(); self.current_doc = None
        gc.collect()
        paper = self.cb_pap.currentText().replace("纸张: ", "") if "纸张: " in self.cb_pap.currentText() else self.cb_pap.currentText()
        self.current_doc = PDFEngine.merge([x['p'] for x in self.data], m, paper, o, self.chk_cut.isChecked(), out_path=None)
        page_imgs = []
        if self.current_doc:
            for page in self.current_doc: 
                # 使用平台自适应的渲染分辨率
                scale = UI_CONFIG.get("preview_render_scale", 4.0)
                pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=True, annots=True); img = QImage.fromData(pix.tobytes("png"))
                if rotate_preview:
                    transform = QTransform()
                    transform.rotate(-90) 
                    img = img.transformed(transform)
                page_imgs.append(img)
        self.word_preview.show_pages(page_imgs)

    def add_files(self, fs):
        """添加文件并异步执行 OCR 识别"""
        logger = logging.getLogger(__name__)
        logger.info(f"开始添加 {len(fs)} 个文件")
        
        try:
            s = QSettings("MySoft", "InvoiceMaster")
            ak, sk = s.value("ak"), s.value("sk")
            
            # 显示导入进度对话框
            import_progress = ProgressDialog(self, "发票导入中", can_cancel=False)
            import_progress.show()
            QApplication.processEvents()
            
            # 先同步添加所有文件到列表（快速响应用户）
            files_with_index = []
            start_idx = len(self.data)
            
            added_count = 0
            total_files = len(fs)
            
            for i, f in enumerate(fs):
                try:
                    # [V3.5] 文件名预过滤：直接跳过明确的非发票文件
                    # 包含：清单、入住凭证、行程报销单、结算单
                    logger.info(f"添加文件: {os.path.basename(f)}")
                    # [V3.5] 移除文件名过滤，允许所有文件导入，但在统计时排除
                    basename = os.path.basename(f)
                    # ignore_keywords = ["清单", "入住凭证", "行程报销单", "结算单"]
                    # if any(k in basename for k in ignore_keywords):
                    #     logger.info(f"🚫 根据文件名跳过: {basename}")
                    #     continue

                    logger.info(f"添加文件: {basename}")
                    
                    # 更新导入进度
                    import_progress.update_progress(i + 1, total_files, basename)
                    
                    d = {"p": f, "n": basename, "d": "", "a": 0.0, "ext": {}, "_pending_ocr": True}
                    
                    # 本地解析完整发票信息
                    # 本地解析完整发票信息
                    if f.lower().endswith(".pdf"):
                        local_result = InvoiceHelper.parse_invoice_local(f)
                        
                        # [V3.5] 特殊处理：如果是清单或非发票凭证，直接认可，跳过OCR
                        inv_type = local_result.get("invoice_type", "") if local_result else ""
                        is_special_doc = "清单" in inv_type or "非发票" in inv_type
                        
                        if is_special_doc:
                             d["a"] = local_result.get("amount", 0)
                             d["d"] = local_result.get("date", "")
                             d["ext"] = local_result
                             d["_pending_ocr"] = False # 明确标记不需OCR
                             logger.info(f"✅ 识别为特殊文档(不计入统计): {os.path.basename(f)} - {inv_type}")
                             
                        # 只有当数据完整时才跳过OCR
                        elif InvoiceHelper._is_result_complete(local_result):
                            d["a"] = local_result["amount"]
                            d["d"] = local_result.get("date", "")
                            d["ext"] = local_result
                            d["_pending_ocr"] = False  # 数据完整，不需要OCR
                            logger.info(f"✅ 本地解析完整: {os.path.basename(f)}, 金额: {d['a']}")
                        elif local_result.get("amount", 0) > 0:
                            # 有金额但不完整，需要继续OCR
                            d["a"] = local_result["amount"]
                            d["d"] = local_result.get("date", "")
                            d["ext"] = local_result
                            d["_pending_ocr"] = True  # 数据不完整，需要OCR补充
                            logger.info(f"⚠️ 本地解析不完整: {os.path.basename(f)}, 金额: {d['a']}，将使用OCR")
                        else:
                            logger.info(f"⚠️ 本地解析失败: {os.path.basename(f)}，将使用OCR")
                    
                    item = QListWidgetItem(self.list)
                    item.setSizeHint(QSize(250, 60))
                    widget = InvoiceItemWidget(d, item, self.delete_specific_item)
                    self.list.setItemWidget(item, widget)
                    
                    
                    # [V3.5] 财务严谨性过滤：虽然导入清单/凭证，但不计入统计
                    # 之前的版本是直接跳过(continue)，现在改为导入但标记类型
                    skipped_types = ["发票清单", "非发票凭证"]
                    base_invoicetype = d.get("invoice_type", "")
                    if base_invoicetype in skipped_types or "非发票" in base_invoicetype:
                         # 可以在这里做一些额外的UI标记，目前仅依靠 calc() 排除统计
                         pass
                    
                    self.data.append(d)
                    widget.update_display(d)
                    self._save_d_to_db(d)
                    added_count += 1
                    
                    # 记录需要 OCR 的文件（只有 _pending_ocr=True 的才需要）
                    # 如果有百度API Key 或 私有OCR地址，就添加到待识别列表
                    private_ocr_url = QSettings("MySoft", "InvoiceMaster").value("private_ocr_url", "")
                    if (ak or private_ocr_url) and d.get("_pending_ocr", True):
                        files_with_index.append((start_idx + i, f))
                
                except Exception as inner_e:
                    logger.error(f"处理单个文件失败 {f}: {str(inner_e)}", exc_info=True)
                    continue

            # 关闭导入进度对话框
            import_progress.close()
            
            self.calc()
            self.show_layout_preview()
            QApplication.processEvents()
            
            # 如果有需要识别的文件，启动异步 OCR
            if files_with_index:
                self._start_async_ocr(files_with_index, ak, sk)
            else:
                logger.info(f"文件添加完成，共 {len(self.data)} 个发票（无 OCR）")
                self.sort_by_invoice_type()  # 自动按类型分组排序
        except Exception as e:
            logger.error(f"添加文件全局错误: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "导入失败", f"添加文件时发生错误:\n{str(e)}")
    
    def _start_async_ocr(self, files_with_index, ak, sk):
        """启动异步 OCR 处理"""
        logger = logging.getLogger(__name__)
        logger.info(f"启动异步 OCR，共 {len(files_with_index)} 个文件")
        
        # 创建进度对话框
        self.progress_dialog = ProgressDialog(self, "OCR 识别中", can_cancel=True)
        
        # 创建 OCR 工作线程
        self.ocr_worker = OcrWorker(files_with_index, ak, sk, self)
        self.ocr_worker.progress.connect(self._on_ocr_progress)
        self.ocr_worker.result.connect(self._on_ocr_result)
        self.ocr_worker.error.connect(self._on_ocr_error)
        self.ocr_worker.finished_all.connect(self._on_ocr_finished)
        
        # 取消处理
        self.progress_dialog.cancelled.connect(self.ocr_worker.cancel)
        
        # 启动工作线程和显示对话框
        self.ocr_worker.start()
        self.progress_dialog.show()
    
    def _on_ocr_progress(self, current, total, filename):
        """OCR 进度更新"""
        if self.progress_dialog:
            self.progress_dialog.update_progress(current, total, filename)
    
    def _on_ocr_result(self, idx, result):
        """OCR 单个结果返回"""
        logger = logging.getLogger(__name__)
        if idx < len(self.data):
            d = self.data[idx]
            d["_pending_ocr"] = False
            
            if result:
                if "amount" in result:
                    d["a"] = result["amount"]
                if "date" in result:
                    d["d"] = result["date"]
                d["ext"] = result
                logger.info(f"OCR 结果已更新: {d['n']}, 金额: {d.get('a', 0)}")
                self._save_d_to_db(d)

            
            # 更新列表项显示
            item = self.list.item(idx)
            if item:
                widget = self.list.itemWidget(item)
                if widget:
                    widget.update_display(d)
            
            # 更新统计
            self.calc()
    
    def _on_ocr_error(self, idx, error_msg):
        """OCR 单个错误处理"""
        logger = logging.getLogger(__name__)
        if idx < len(self.data):
            d = self.data[idx]
            d["_pending_ocr"] = False
            logger.warning(f"OCR 失败 [{d['n']}]: {error_msg}")
    
    def _on_ocr_finished(self):
        """OCR 全部完成"""
        logger = logging.getLogger(__name__)
        logger.info(f"异步 OCR 处理完成，共 {len(self.data)} 个发票")
        
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self.ocr_worker = None
        self.sort_by_invoice_type()  # 自动按类型分组排序
        self.calc()
        self.show_layout_preview()

    # ── 发票分类排序优先级 ──
    INVOICE_TYPE_ORDER = {
        "增值税专用发票": 0,
        "增值税普通发票": 1,
        "增值税电子普通发票": 2,
        "电子发票": 3,
        "增值税发票": 4,
        "铁路电子客票": 5,
        "财政电子票据": 6,
        "发票清单": 7,
        "非发票凭证": 8,
    }

    def _get_type_sort_key(self, d):
        """获取发票的分类排序键"""
        inv_type = d.get("ext", {}).get("invoice_type", "")
        # 精确匹配
        if inv_type in self.INVOICE_TYPE_ORDER:
            return self.INVOICE_TYPE_ORDER[inv_type]
        # 模糊匹配（处理类似 "非发票凭证-入住" 等变体）
        for key, order in self.INVOICE_TYPE_ORDER.items():
            if key in inv_type or inv_type in key:
                return order
        return 99  # 未分类排最后

    def sort_by_invoice_type(self):
        """按发票类型分组排序，同类型发票排在一起"""
        logger = logging.getLogger(__name__)
        if len(self.data) <= 1:
            return
        
        # 按类型排序，同类型内保持原始导入顺序（stable sort）
        self.data.sort(key=self._get_type_sort_key)
        
        # 刷新列表显示
        self.list.clear()
        for d in self.data:
            item = QListWidgetItem(self.list)
            item.setSizeHint(QSize(250, 60))
            widget = InvoiceItemWidget(d, item, self.delete_specific_item)
            self.list.setItemWidget(item, widget)
            widget.update_display(d)
        
        # 记录排序结果
        type_counts = {}
        for d in self.data:
            t = d.get("ext", {}).get("invoice_type", "未分类") or "未分类"
            type_counts[t] = type_counts.get(t, 0) + 1
        logger.info(f"发票已按类型分组排序: {type_counts}")

    def calc(self):
        """计算统计信息（仅计算有效发票，排除清单和非发票凭证）"""
        total_n = 0
        total_a = 0.0
        unrecognized_n = 0  # 未识别数量
        
        ignored_types = ["发票清单", "非发票凭证"]
        
        for d in self.data:
            # [修复] 从 ext 中读取 invoice_type（而非 d 直接读取）
            inv_type = d.get("ext", {}).get("invoice_type", "")
            # 排除清单和非发票凭证
            if inv_type in ignored_types or "非发票" in inv_type:
                continue
            
            # 统计未识别发票（金额为0或无日期）
            amount = d.get("a", 0)
            date = d.get("d", "")
            if amount == 0 or not date:
                unrecognized_n += 1
            
            total_n += 1
            total_a += amount
        
        # 显示格式：已识别数量 + 未识别数量
        self.lbl_inf.setText(f"{total_n}")
        if unrecognized_n > 0:
            self.lbl_inf.setToolTip(f"{total_n} 张发票，{unrecognized_n} 张未识别")
        self.lbl_tot.setText(f"¥{total_a:,.2f}")
        
        # 更新清单徽标
        if hasattr(self, 'list_count_badge'):
            self.list_count_badge.setText(str(len(self.data)))
            if len(self.data) > 0:
                self.list_count_badge.setStyleSheet("background: #DBEAFE; color: #2563EB; border-radius: 9px; font-size: 11px; font-weight: 600;")
            else:
                self.list_count_badge.setStyleSheet("background: #E2E8F0; color: #64748B; border-radius: 9px; font-size: 11px; font-weight: 600;")
    def clear(self): self.list.clear(); self.data=[]; self.calc(); self.trigger_refresh()
    def ctx_menu(self, p): m=QMenu(); a=QAction("删除",self); a.triggered.connect(self.del_sel); m.addAction(a); m.exec(self.list.mapToGlobal(p))
    def del_sel(self):
        for r in sorted([self.list.row(i) for i in self.list.selectedItems()], reverse=True): 
            self.list.takeItem(r); 
            d = self.data.pop(r)
            get_db().delete_invoice(d['p'])
        self.calc(); self.trigger_refresh()
    def xls(self):
        logger = logging.getLogger(__name__)
        if not self.data: return
        
        # 激活功能已移除，直接进行导出
        
        logger.info(f"开始导出 Excel: {len(self.data)} 条数据")
        
        # 读取上次保存的路径
        s = QSettings("MySoft", "InvoiceMaster")
        last_path = s.value("last_excel_path", os.path.expanduser("~/Desktop/invoice_report.xlsx"))
        
        # 先检查默认路径文件是否存在，提供中文选项
        file_action = "new"  # new=新建, append=追加, overwrite=覆盖
        
        if os.path.exists(last_path):
            # 文件已存在，显示中文选择对话框
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("文件已存在")
            msg_box.setText(f"文件 \"{os.path.basename(last_path)}\" 已存在。\n\n请选择操作方式：")
            msg_box.setIcon(QMessageBox.Icon.Question)
            
            append_btn = msg_box.addButton("📥 追加数据", QMessageBox.ButtonRole.AcceptRole)
            overwrite_btn = msg_box.addButton("🔄 覆盖文件", QMessageBox.ButtonRole.DestructiveRole)
            newfile_btn = msg_box.addButton("📁 另存为...", QMessageBox.ButtonRole.ActionRole)
            cancel_btn = msg_box.addButton("取消", QMessageBox.ButtonRole.RejectRole)
            
            msg_box.exec()
            clicked = msg_box.clickedButton()
            
            if clicked == cancel_btn:
                return
            elif clicked == append_btn:
                file_action = "append"
                p = last_path
            elif clicked == overwrite_btn:
                file_action = "overwrite"
                p = last_path
            elif clicked == newfile_btn:
                # 用户选择另存为，打开文件对话框
                p, _ = QFileDialog.getSaveFileName(self, "保存 Excel 报表", last_path, "Excel (*.xlsx)",
                                                   options=QFileDialog.Option.DontConfirmOverwrite)
                if not p: return
                file_action = "overwrite" if os.path.exists(p) else "new"
        else:
            # 文件不存在，使用默认路径或让用户选择
            p, _ = QFileDialog.getSaveFileName(self, "保存 Excel 报表", last_path, "Excel (*.xlsx)",
                                               options=QFileDialog.Option.DontConfirmOverwrite)
            if not p: return
            
            # 检查用户选择的新路径是否存在
            if os.path.exists(p):
                reply = QMessageBox.question(
                    self, "确认覆盖",
                    f"文件 \"{os.path.basename(p)}\" 已存在。\n\n是否覆盖该文件？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
                file_action = "overwrite"
        
        # 保存路径供下次使用
        s.setValue("last_excel_path", p)
        
        try:
            # 准备新数据 - 18个专业字段
            new_rows = []
            from datetime import datetime
            import_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            export_idx = 1
            for x in self.data:
                ext = x.get("ext", {})
                
                # [V3.5] 导出过滤：清单和非发票凭证不导出到Excel
                # 这些只是为了管理查看，不应进入财务报表
                inv_type = ext.get("invoice_type", "")
                skipped_types = ["发票清单", "非发票凭证"]
                if inv_type in skipped_types or "非发票" in inv_type:
                    continue
                
                # 处理金额字段,确保是数值类型
                try: amount = float(x.get("a", 0) or 0)
                except: amount = 0
                try: amount_without_tax = float(ext.get("amount_without_tax", "") or 0)
                except: amount_without_tax = ""
                try: tax_amt = float(ext.get("tax_amt", "") or 0)
                except: tax_amt = ""
                
                # [V3.6.5] 导出时字段补充逻辑（独立于OCR优先级）
                # 如果关键字段为空，尝试从PDF重新解析获取
                code = ext.get("code", "")
                number = ext.get("number", "")
                check_code = ext.get("check_code", "")
                seller = ext.get("seller", "")
                seller_tax_id = ext.get("seller_tax_id", "")
                buyer = ext.get("buyer", "")
                buyer_tax_id = ext.get("buyer_tax_id", "")
                
                # [暂时禁用] 重新解析逻辑导致导出按钮无响应，需要进一步调试
                # file_path = x.get("p", "")
                # if file_path and file_path.lower().endswith(".pdf"):
                #     need_reparse = not code or not number or not seller or not seller_tax_id
                #     if need_reparse:
                #         ... 重新解析逻辑 ...
                
                # 标准导出字段
                row_data = {
                    "序号": export_idx,
                    "开票日期": x.get("d", ""), 
                    "发票类型": ext.get("invoice_type", ""),
                    "发票代码": code, 
                    "发票号码": number, 
                    "校验码": check_code[-6:] if check_code else "",
                    "购买方名称": buyer,
                    "购买方税号": buyer_tax_id,
                    "销售方名称": seller, 
                    "销售方税号": seller_tax_id,
                    "不含税金额": amount_without_tax,
                    "税率": ext.get("tax_rate", ""),
                    "税额": tax_amt,
                    "价税合计": amount,
                    "商品明细": ext.get("item_name", ""),
                    "备注": ext.get("remark", ""),
                    "导入时间": import_time,
                    "文件路径": x.get("p", "")
                }
                
                new_rows.append(row_data)
                export_idx += 1
            
            new_df = pd.DataFrame(new_rows)
            # 确保列顺序
            fields = ["序号", "开票日期", "发票类型", "发票代码", "发票号码", "校验码", 
                     "购买方名称", "购买方税号", "销售方名称", "销售方税号", 
                     "不含税金额", "税率", "税额", "价税合计", "商品明细", "备注", "导入时间", "文件路径"]
            new_df = new_df[fields]
            
            # 根据用户选择决定是追加还是覆盖
            if file_action == "append" and os.path.exists(p):
                try:
                    existing_df = pd.read_excel(p)
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                    is_append = True
                except Exception:
                    combined_df = new_df
                    is_append = False
            else:
                combined_df = new_df
                is_append = False
            
            # 保存到 Excel
            combined_df.to_excel(p, index=False, engine='openpyxl')
            
            # 使用 openpyxl 添加专业样式
            try:
                from openpyxl import load_workbook
                from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
                from openpyxl.utils import get_column_letter
                
                wb = load_workbook(p)
                ws = wb.active
                
                # 定义样式
                header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
                header_font = Font(color="FFFFFF", bold=True, size=11)
                header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
                yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
                zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
                thin_border = Border(
                    left=Side(style='thin', color='E2E8F0'),
                    right=Side(style='thin', color='E2E8F0'),
                    top=Side(style='thin', color='E2E8F0'),
                    bottom=Side(style='thin', color='E2E8F0')
                )
                
                # 应用表头样式
                for col_idx in range(1, ws.max_column + 1):
                    cell = ws.cell(row=1, column=col_idx)
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = header_align
                    cell.border = thin_border
                
                # 冻结首行
                ws.freeze_panes = "A2"
                
                # 建立字段到列索引的映射 (1-based)
                field_list = ["序号", "开票日期", "发票类型", "发票代码", "发票号码", "校验码", 
                             "购买方名称", "购买方税号", "销售方名称", "销售方税号", 
                             "不含税金额", "税率", "税额", "价税合计", "商品明细", "备注", "导入时间", "文件路径"]
                col_map = {field: i+1 for i, field in enumerate(field_list)}
                
                # 设置列宽
                field_widths = {
                    "序号": 6, "开票日期": 12, "发票类型": 14, "发票代码": 14, "发票号码": 12,
                    "校验码": 10, "购买方名称": 25, "购买方税号": 22, "销售方名称": 25, "销售方税号": 22,
                    "不含税金额": 12, "税率": 8, "税额": 12, "价税合计": 14, "商品明细": 30,
                    "备注": 20, "导入时间": 18, "文件路径": 40
                }
                for i, field in enumerate(field_list, 1):
                    if field in field_widths:
                        ws.column_dimensions[get_column_letter(i)].width = field_widths[field]
                
                # 检测重复发票：发票号码 + 开票日期 + 金额 三者都相同才算重复
                # [V3.6.5] 增强：如果发票号码为空，使用文件名+金额作为备选
                invoice_keys = {}
                duplicate_rows = set()
                num_col_idx = col_map.get("发票号码")
                date_col_idx = col_map.get("开票日期")
                amount_col_idx = col_map.get("价税合计")
                path_col_idx = col_map.get("文件路径")
                
                for row_idx in range(2, ws.max_row + 1):
                    invoice_num = ws.cell(row=row_idx, column=num_col_idx).value if num_col_idx else ""
                    invoice_date = ws.cell(row=row_idx, column=date_col_idx).value if date_col_idx else ""
                    invoice_amount = ws.cell(row=row_idx, column=amount_col_idx).value if amount_col_idx else ""
                    file_path = ws.cell(row=row_idx, column=path_col_idx).value if path_col_idx else ""
                    
                    # 构建唯一键
                    if invoice_num and str(invoice_num).strip():
                        # 优先使用：发票号码 + 日期 + 金额
                        key = f"NUM:{invoice_num}|{invoice_date}|{invoice_amount}"
                    elif file_path:
                        # 备选使用：文件名 + 金额（针对没有解析出发票号码的情况）
                        filename = os.path.basename(str(file_path))
                        key = f"FILE:{filename}|{invoice_amount}"
                    else:
                        continue  # 没有任何可判断的信息，跳过
                    
                    if key in invoice_keys:
                        duplicate_rows.add(row_idx)
                        duplicate_rows.add(invoice_keys[key])
                    else:
                        invoice_keys[key] = row_idx
                
                # 金额列索引
                amount_cols = [col_map.get(f) for f in ["不含税金额", "税额", "价税合计"] if f in col_map]
                
                # 应用数据行样式(斑马纹 + 重复标记)
                for row_idx in range(2, ws.max_row + 1):
                    is_duplicate = row_idx in duplicate_rows
                    is_zebra = row_idx % 2 == 0
                    for col_idx in range(1, ws.max_column + 1):
                        cell = ws.cell(row=row_idx, column=col_idx)
                        cell.border = thin_border
                        if is_duplicate:
                            cell.fill = yellow_fill
                        elif is_zebra:
                            cell.fill = zebra_fill
                        # 金额列右对齐
                        if col_idx in amount_cols:
                            cell.alignment = Alignment(horizontal="right")
                
                # 添加底部统计行
                # 计算总金额
                total_amount = 0
                amount_col_idx = col_map.get("价税合计")
                
                if amount_col_idx:
                    for row_idx in range(2, ws.max_row + 1):  # 遍历到现有最大行
                        try:
                            val = ws.cell(row=row_idx, column=amount_col_idx).value
                            if val: total_amount += float(val)
                        except: pass
                
                stat_row = ws.max_row + 1
                
                # 在第一列或"序号"列显示"统计"
                label_col = col_map.get("序号", 1)
                ws.cell(row=stat_row, column=label_col, value="统计").font = Font(bold=True)
                
                # 在第二列或"开票日期"列显示数量
                count_col = col_map.get("开票日期", 2)
                ws.cell(row=stat_row, column=count_col, value=f"共 {len(new_rows)} 张发票")
                
                # 显示总金额
                if amount_col_idx:
                    ws.cell(row=stat_row, column=amount_col_idx, value=f"¥{total_amount:,.2f}").font = Font(bold=True, color="DC2626")
                
                # 添加工作表保护(安全锁定功能)
                # 允许: 选择单元格、复制、排序、筛选、查找
                # 禁止: 编辑内容、删除行列、修改格式、插入行列
                from openpyxl.worksheet.protection import SheetProtection
                SHEET_PASSWORD = "InvoiceMaster2024"  # 保护密码
                
                ws.protection = SheetProtection(
                    sheet=True,
                    password=SHEET_PASSWORD,
                    selectLockedCells=False,
                    selectUnlockedCells=False,
                    sort=False,
                    autoFilter=False,
                    formatCells=True,
                    formatColumns=True,
                    formatRows=True,
                    insertColumns=True,
                    insertRows=True,
                    insertHyperlinks=True,
                    deleteColumns=True,
                    deleteRows=True,
                    objects=False,
                    scenarios=False,
                    pivotTables=False,
                )
                logger.info("Excel 工作表保护已启用")
                
                wb.save(p)
                
                # 提示信息
                if is_append:
                    msg = f"✅ 已追加 {len(new_df)} 条数据到现有文件！\n"
                    logger.info(f"Excel 追加成功: {p}, 新增 {len(new_df)} 条")
                else:
                    msg = f"✅ 已导出 {len(new_df)} 条数据！\n"
                    logger.info(f"Excel 导出成功: {p}, 共 {len(new_df)} 条")
                
                msg += f"💰 价税合计: ¥{total_amount:,.2f}\n"
                
                if duplicate_rows:
                    msg += f"⚠️ 检测到 {len(duplicate_rows)//2} 组重复发票（已用黄色标记）\n"
                    logger.warning(f"检测到 {len(duplicate_rows)} 条重复发票")
                else:
                    msg += "✓ 未检测到重复发票\n"
                
                msg += "🔒 工作表已保护，仅允许查看和复制"
                
                # 激活功能已移除
                
                QMessageBox.information(self, "导出成功", msg)
                
            except Exception as e:
                # 如果颜色标记失败，至少数据已保存
                logger.warning(f"Excel 颜色标记失败: {str(e)}")
                QMessageBox.information(self, "导出成功", f"数据已导出，但颜色标记失败: {str(e)}")
                
        except Exception as e:
            logger.error(f"Excel 导出失败: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "导出失败", f"错误: {str(e)}")
    def run(self):
        """执行打印操作（异步）"""
        if not self.data: 
            return QMessageBox.warning(self, "Tips", "请先添加发票")
        
        self.btn_go.setText("处理中...")
        self.btn_go.setEnabled(False)
        QApplication.processEvents()
        
        # 准备参数
        m = "1x1"
        m = "1x2" if self.b2.isChecked() else m
        m = "2x2" if self.b4.isChecked() else m
        o = "H" if self.rd_l.isChecked() else "V"
        out = os.path.expanduser("~/Desktop/Print_Job.pdf")
        
        if out not in self.temp_files:
            self.temp_files.append(out)
        
        paper = self.cb_pap.currentText().replace("纸张: ", "") if "纸张: " in self.cb_pap.currentText() else self.cb_pap.currentText()
        
        # 保存打印参数供回调使用
        self._print_params = {
            "out_path": out,
            "open_only": self.cb_pr.currentIndex() == 0,
            "copies": self.sp_cpy.value(),
            "force_rotate": self.chk_rotate.isChecked()
        }
        
        # 使用异步 PDF 合并
        files = [x["p"] for x in self.data]
        self.pdf_worker = PdfWorker(files, m, paper, o, self.chk_cut.isChecked(), out, self)
        self.pdf_worker.progress.connect(self._on_pdf_progress)
        self.pdf_worker.finished.connect(self._on_pdf_merge_finished)
        self.pdf_worker.error.connect(self._on_pdf_error)
        self.pdf_worker.start()
    
    def _on_pdf_progress(self, current, total):
        """PDF 合并进度"""
        self.btn_go.setText(f"合并 PDF ({current}/{total})...")
        QApplication.processEvents()
    
    def _on_pdf_merge_finished(self, out_path):
        """PDF 合并完成，开始打印"""
        self.pdf_worker = None
        params = self._print_params
        
        if params["open_only"]:
            # 仅打开 PDF
            if platform.system() == "Windows":
                os.startfile(out_path, "print")
            elif platform.system() == "Darwin":
                os.system(f"open '{out_path}'")
            else:
                os.system(f"xdg-open '{out_path}'")
            self.btn_go.setText(" 开始打印")
            self.btn_go.setEnabled(True)
        else:
            # 异步打印
            self._start_async_print(out_path, params["copies"], params["force_rotate"])
    
    def _on_pdf_error(self, error_msg):
        """PDF 合并错误"""
        self.pdf_worker = None
        self.btn_go.setText("重试")
        self.btn_go.setEnabled(True)
        QMessageBox.critical(self, "Error", error_msg)
    
    def _start_async_print(self, pdf_path, copies, force_rotate):
        """启动异步打印"""
        p_name = self.cb_pr.currentText().replace("🖨️ ", "")
        self.btn_go.setText(f"正在发送至 {p_name}...")
        
        self.print_worker = PrintWorker(pdf_path, self.current_printer, copies, force_rotate, self)
        self.print_worker.progress.connect(self._on_print_progress)
        self.print_worker.finished.connect(self._on_print_finished)
        self.print_worker.start()
    
    def _on_print_progress(self, current, total):
        """打印进度"""
        self.btn_go.setText(f"打印中 ({current}/{total})...")
        QApplication.processEvents()
    
    def _on_print_finished(self, success, msg):
        """打印完成"""
        self.print_worker = None
        self.btn_go.setText(" 开始打印")
        self.btn_go.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "完成", "已发送")
        else:
            QMessageBox.critical(self, "错误", msg)
