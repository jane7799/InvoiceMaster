
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QFrame, QPushButton, QFileDialog, QProgressBar,
                           QGraphicsDropShadowEffect)
from PyQt6.QtGui import QColor, QPainter, QBrush, QLinearGradient, QPainterPath, QPen, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRectF, QTimer, QVariantAnimation
from src.utils.icons import Icons
from src.utils.constants import APP_NAME, APP_VERSION

from src.utils.config import UI_CONFIG

class Card(QFrame):
    def __init__(self):
        super().__init__(); self.setObjectName("Card")
        # 使用平台自适应阴影配置
        blur = UI_CONFIG.get("shadow_blur", 25)
        opacity = UI_CONFIG.get("shadow_opacity", 25)
        eff = QGraphicsDropShadowEffect()
        eff.setBlurRadius(blur)
        eff.setColor(QColor(0, 0, 0, opacity))
        eff.setOffset(0, 2 if UI_CONFIG.get("is_legacy") else 4)
        self.setGraphicsEffect(eff)

class GlassCard(QFrame):
    """毛玻璃质感卡片"""
    def __init__(self):
        super().__init__()
        self.setObjectName("GlassCard")
        eff = QGraphicsDropShadowEffect()
        eff.setBlurRadius(20)
        eff.setColor(QColor(0, 0, 0, 15))
        eff.setOffset(0, 4)
        self.setGraphicsEffect(eff)

class DragArea(QWidget):
    dropped = pyqtSignal(list)
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(140)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hover = False
        self._pulse_opacity = 0.0
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        # 脉冲动画
        self._pulse_anim = QVariantAnimation()
        self._pulse_anim.setStartValue(0.0)
        self._pulse_anim.setEndValue(1.0)
        self._pulse_anim.setDuration(2000)
        self._pulse_anim.setLoopCount(-1)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_anim.valueChanged.connect(self._on_pulse)
        self._pulse_anim.start()
        
        # 内部布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 图标
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setPixmap(Icons.get("upload", "#FFFFFF").pixmap(38, 38))
        self.icon_label.setStyleSheet("background: transparent;")
        self.icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.icon_label)
        
        # 提示文字
        self.text_label = QLabel("拖放发票文件到这里")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet("color: rgba(255,255,255,0.95); font-size: 14px; font-weight: 600; background: transparent;")
        self.text_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.text_label)
        
        # 次要文字
        self.sub_label = QLabel("支持 PDF / JPG / PNG 格式")
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_label.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 11px; font-weight: 400; background: transparent;")
        self.sub_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.sub_label)
    
    def _on_pulse(self, val):
        self._pulse_opacity = val
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # 创建圆角矩形路径
        path = QPainterPath()
        path.addRoundedRect(0.0, 0.0, float(w), float(h), 16.0, 16.0)
        
        # 创建渐变背景
        gradient = QLinearGradient(0, 0, w, h)
        use_gradients = UI_CONFIG.get("use_gradients", True)
        
        if self._hover:
            if use_gradients:
                gradient.setColorAt(0, QColor("#1D4ED8"))
                gradient.setColorAt(0.5, QColor("#1E40AF"))
                gradient.setColorAt(1, QColor("#1E3A8A"))
            else:
                gradient.setColorAt(0, QColor("#1D4ED8"))
                gradient.setColorAt(1, QColor("#1D4ED8"))
        else:
            if use_gradients:
                gradient.setColorAt(0, QColor("#3B82F6"))
                gradient.setColorAt(0.5, QColor("#2563EB"))
                gradient.setColorAt(1, QColor("#1D4ED8"))
            else:
                gradient.setColorAt(0, QColor("#2563EB"))
                gradient.setColorAt(1, QColor("#2563EB"))
        
        painter.fillPath(path, QBrush(gradient))
        
        # 绘制微光脉冲效果（仅非悬停时）
        if not self._hover and use_gradients:
            pulse_alpha = int(20 * self._pulse_opacity)
            pulse_gradient = QLinearGradient(0, 0, w, 0)
            pulse_gradient.setColorAt(0, QColor(255, 255, 255, 0))
            pulse_gradient.setColorAt(max(0, self._pulse_opacity - 0.2), QColor(255, 255, 255, 0))
            pulse_gradient.setColorAt(self._pulse_opacity, QColor(255, 255, 255, pulse_alpha))
            pulse_gradient.setColorAt(min(1, self._pulse_opacity + 0.2), QColor(255, 255, 255, 0))
            pulse_gradient.setColorAt(1, QColor(255, 255, 255, 0))
            painter.fillPath(path, QBrush(pulse_gradient))
        
        # 绘制虚线边框
        if not self._hover:
            pen = QPen(QColor(255, 255, 255, 60))
            pen.setWidth(2)
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setDashPattern([6, 4])
            painter.setPen(pen)
            inner_path = QPainterPath()
            inner_path.addRoundedRect(4.0, 4.0, float(w - 8), float(h - 8), 12.0, 12.0)
            painter.drawPath(inner_path)
        
        painter.end()
    
    def upd(self, c): 
        # 始终使用白色图标
        self.icon_label.setPixmap(Icons.get("upload", "#FFFFFF").pixmap(38, 38))
    
    def enterEvent(self, e):
        self._hover = True
        self.text_label.setText("点击选择文件")
        self.update()
        
    def leaveEvent(self, e):
        self._hover = False
        self.text_label.setText("拖放发票文件到这里")
        self.update()
        
    def dragEnterEvent(self, e):
        self._hover = True
        self.text_label.setText("释放以添加文件")
        self.update()
        e.accept()
        
    def dragLeaveEvent(self, e):
        self._hover = False
        self.text_label.setText("拖放发票文件到这里")
        self.update()
        
    def dropEvent(self, e):
        self._hover = False
        self.text_label.setText("拖放发票文件到这里")
        self.update()
        self.dropped.emit([u.toLocalFile() for u in e.mimeData().urls() if u.toLocalFile().lower().endswith(('.pdf','.jpg','.png'))])
        
    def mousePressEvent(self, e): 
        fs, _ = QFileDialog.getOpenFileNames(self, "添加发票", "", "发票文件 (*.pdf *.jpg *.png)")
        if fs: self.dropped.emit(fs)

class InvoiceItemWidget(QWidget):
    def __init__(self, data, parent_item, delete_callback):
        super().__init__()
        self.data = data
        self.parent_item = parent_item
        self.delete_callback = delete_callback
        self.setObjectName("ItemRow")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        
        # 类型指示条
        self.type_indicator = QFrame()
        self.type_indicator.setFixedSize(3, 36)
        self.type_indicator.setStyleSheet("background: #3B82F6; border-radius: 1.5px;")
        layout.addWidget(self.type_indicator)
        
        # 文件图标
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(34, 34)
        self.icon_lbl.setPixmap(Icons.get("file", "#94A3B8").pixmap(28, 28))
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setStyleSheet("background: #F1F5F9; border-radius: 8px; padding: 3px;")
        layout.addWidget(self.icon_lbl)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)
        
        # 标题行（包含文件名和状态标识）
        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        
        self.lbl_title = QLabel(data['n'])
        self.lbl_title.setObjectName("ItemTitle")
        self.lbl_title.setStyleSheet("font-size: 12px;")
        title_row.addWidget(self.lbl_title)
        
        # 状态标识
        self.status_badge = QLabel()
        self.status_badge.setFixedSize(20, 20)
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.hide()
        title_row.addWidget(self.status_badge)
        title_row.addStretch()
        
        text_layout.addLayout(title_row)
        
        # 详情行
        self.lbl_detail = QLabel(f"{data['d']} | ¥{data['a']:.2f}")
        self.lbl_detail.setObjectName("ItemDetail")
        self.lbl_detail.setStyleSheet("font-size: 11px;")
        text_layout.addWidget(self.lbl_detail)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # 金额标签（突出显示）
        self.amount_label = QLabel(f"¥{data['a']:.2f}")
        self.amount_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #2563EB;")
        layout.addWidget(self.amount_label)
        
        self.btn_del = QPushButton()
        self.btn_del.setObjectName("RowDelBtn")
        self.btn_del.setIcon(Icons.get("trash", "#CBD5E1"))
        self.btn_del.setFixedSize(28, 28)
        self.btn_del.setToolTip("删除此发票")
        self.btn_del.clicked.connect(self.on_delete_clicked)
        layout.addWidget(self.btn_del)
        
        self.update_status_badge()
    
    def on_delete_clicked(self):
        self.delete_callback(self.parent_item)
    
    def update_display(self, new_data):
        self.data = new_data
        self.lbl_title.setText(new_data['n'])
        
        # 详情只显示日期（金额单独显示）
        date_str = new_data.get('d', '')
        self.lbl_detail.setText(date_str if date_str else "日期未识别")
        
        # 金额突出显示
        amount = new_data.get('a', 0)
        self.amount_label.setText(f"¥{amount:.2f}")
        if amount > 0:
            self.amount_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #2563EB;")
        else:
            self.amount_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #CBD5E1;")
        
        self.update_status_badge()
    
    def update_status_badge(self):
        """更新状态标识"""
        has_amount = self.data.get('a', 0) > 0
        is_manually_edited = self.data.get('manually_edited', False)
        
        if not has_amount:
            self.status_badge.setText("!")
            self.status_badge.setStyleSheet("""
                background: #FEE2E2; border-radius: 10px; font-size: 11px; 
                color: #DC2626; font-weight: 700;
            """)
            self.status_badge.setToolTip("未识别到金额，请双击修改")
            self.status_badge.show()
            self.type_indicator.setStyleSheet("background: #F87171; border-radius: 1.5px;")
            self.setStyleSheet("""
                QWidget#ItemRow { 
                    background: rgba(254, 226, 226, 0.3); 
                    border-radius: 10px;
                }
            """)
        elif is_manually_edited:
            self.status_badge.setText("✓")
            self.status_badge.setStyleSheet("""
                background: #D1FAE5; border-radius: 10px; font-size: 11px; 
                color: #059669; font-weight: 700;
            """)
            self.status_badge.setToolTip("已手动修改金额")
            self.status_badge.show()
            self.type_indicator.setStyleSheet("background: #10B981; border-radius: 1.5px;")
            self.setStyleSheet("""
                QWidget#ItemRow { 
                    background: rgba(209, 250, 229, 0.2); 
                    border-radius: 10px;
                }
            """)
        else:
            self.status_badge.hide()
            self.type_indicator.setStyleSheet("background: #3B82F6; border-radius: 1.5px;")
            self.setStyleSheet("")

class DynamicSplashScreen(QWidget):
    finished = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(520, 340)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 渐变背景卡片
        self.card = QFrame()
        self.card.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1E3A8A,
                    stop:0.3 #2563EB,
                    stop:0.7 #7C3AED,
                    stop:1 #6D28D9
                );
                border-radius: 20px;
            }
        """)
        
        # 阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(37, 99, 235, 120))
        shadow.setOffset(0, 10)
        self.card.setGraphicsEffect(shadow)
        main_layout.addWidget(self.card)
        
        # 卡片内容布局
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(50, 60, 50, 50)
        card_layout.setSpacing(12)
        
        # 应用图标（文字模拟）
        icon_label = QLabel("📄")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 42px; background: transparent; border: none;")
        card_layout.addWidget(icon_label)
        
        card_layout.addSpacing(5)
        
        # 应用名称
        title_lbl = QLabel(APP_NAME)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("""
            color: white;
            font-weight: 700;
            font-size: 26px;
            letter-spacing: 3px;
            background: transparent;
            border: none;
        """)
        card_layout.addWidget(title_lbl)
        
        # 版本号
        ver_lbl = QLabel(APP_VERSION)
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver_lbl.setStyleSheet("""
            color: rgba(255, 255, 255, 0.6);
            font-size: 13px;
            font-weight: 400;
            letter-spacing: 2px;
            background: transparent;
            border: none;
        """)
        card_layout.addWidget(ver_lbl)
        
        card_layout.addSpacing(20)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 255, 255, 0.6),
                    stop:0.5 rgba(255, 255, 255, 1),
                    stop:1 rgba(255, 255, 255, 0.6)
                );
                border-radius: 2px;
            }
        """)
        card_layout.addWidget(self.progress)
        
        card_layout.addSpacing(5)
        
        # 状态文字
        self.status_lbl = QLabel("正在初始化...")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.5); font-size: 12px; background: transparent; border: none;")
        card_layout.addWidget(self.status_lbl)
        
        # 启动模拟加载计时器
        self.timer = self.startTimer(25)
        self.step = 0

    def timerEvent(self, e):
        self.step += 1
        self.progress.setValue(self.step)
        
        if self.step > 100:
            self.killTimer(self.timer)
            self.finished.emit()
            return
            
        if self.step < 30:
            self.status_lbl.setText("正在加载组件...")
        elif self.step < 60:
            self.status_lbl.setText("正在初始化引擎...")
        elif self.step < 90:
            self.status_lbl.setText("即将就绪...")
        else:
            self.status_lbl.setText("启动中...")
