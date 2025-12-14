
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QFrame, QPushButton, QFileDialog, QProgressBar,
                           QGraphicsDropShadowEffect)
from PyQt6.QtGui import QColor, QPainter, QBrush, QLinearGradient, QPainterPath
from PyQt6.QtCore import Qt, pyqtSignal
from src.utils.icons import Icons
from src.utils.constants import APP_NAME, APP_VERSION

# Placeholder UI_CONFIG - mimicking usage
UI_CONFIG = {"use_gradients": True, "shadow_blur": 25, "shadow_opacity": 25, "is_legacy": False}

class Card(QFrame):
    def __init__(self):
        super().__init__(); self.setObjectName("Card")
        # 使用平台自适应阴影配置
        blur = UI_CONFIG.get("shadow_blur", 25)
        opacity = UI_CONFIG.get("shadow_opacity", 25)
        eff = QGraphicsDropShadowEffect(); eff.setBlurRadius(blur); eff.setColor(QColor(0,0,0,opacity)); eff.setOffset(0,4 if not UI_CONFIG.get("is_legacy") else 2); self.setGraphicsEffect(eff)

class DragArea(QWidget):
    dropped = pyqtSignal(list)
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(130)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hover = False
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        # 内部布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 图标
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setPixmap(Icons.get("upload", "#FFFFFF").pixmap(42, 42))
        self.icon_label.setStyleSheet("background: transparent;")
        self.icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.icon_label)
        
        # 提示文字
        self.text_label = QLabel("拖放文件上传")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 13px; font-weight: 500; background: transparent;")
        self.text_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.text_label)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 创建圆角矩形路径
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        
        # 创建渐变
        gradient = QLinearGradient(0, 0, 0, self.height())
        use_gradients = UI_CONFIG.get("use_gradients", True)
        
        if self._hover:
            if use_gradients:
                gradient.setColorAt(0, QColor("#2563EB"))
                gradient.setColorAt(0.5, QColor("#1D4ED8"))
                gradient.setColorAt(1, QColor("#1E40AF"))
            else:
                gradient.setColorAt(0, QColor("#1D4ED8"))
                gradient.setColorAt(1, QColor("#1D4ED8"))
        else:
            if use_gradients:
                gradient.setColorAt(0, QColor("#60A5FA"))
                gradient.setColorAt(0.5, QColor("#3B82F6"))
                gradient.setColorAt(1, QColor("#2563EB"))
            else:
                gradient.setColorAt(0, QColor("#3B82F6"))
                gradient.setColorAt(1, QColor("#3B82F6"))
        
        painter.fillPath(path, QBrush(gradient))
        painter.end()
    
    def upd(self, c): 
        # 始终使用白色图标
        self.icon_label.setPixmap(Icons.get("upload", "#FFFFFF").pixmap(42, 42))
    
    def enterEvent(self, e):
        self._hover = True
        self.update()  # 触发重绘
        
    def leaveEvent(self, e):
        self._hover = False
        self.update()  # 触发重绘
        
    def dragEnterEvent(self, e):
        self._hover = True
        self.update()  # 触发重绘
        e.accept()
        
    def dragLeaveEvent(self, e):
        self._hover = False
        self.update()  # 触发重绘
        
    def dropEvent(self, e):
        self._hover = False
        self.update()  # 触发重绘
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
        layout.setContentsMargins(5, 8, 5, 8)
        layout.setSpacing(10)
        
        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(Icons.get("file", "#888").pixmap(32, 32))
        layout.addWidget(self.icon_lbl)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        # 标题行（包含文件名和状态标识）
        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        
        self.lbl_title = QLabel(data['n'])
        self.lbl_title.setObjectName("ItemTitle")
        title_row.addWidget(self.lbl_title)
        
        # 状态标识
        self.status_badge = QLabel()
        self.status_badge.setFixedSize(18, 18)
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.hide()
        title_row.addWidget(self.status_badge)
        title_row.addStretch()
        
        text_layout.addLayout(title_row)
        
        self.lbl_detail = QLabel(f"{data['d']} | ¥{data['a']:.2f}")
        self.lbl_detail.setObjectName("ItemDetail")
        text_layout.addWidget(self.lbl_detail)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        self.btn_del = QPushButton()
        self.btn_del.setObjectName("RowDelBtn")
        self.btn_del.setIcon(Icons.get("trash", "#d73a49"))
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
        self.lbl_detail.setText(f"{new_data['d']} | ¥{new_data['a']:.2f}")
        self.update_status_badge()
    
    def update_status_badge(self):
        """更新状态标识"""
        has_amount = self.data.get('a', 0) > 0
        is_manually_edited = self.data.get('manually_edited', False)
        
        if not has_amount:
            self.status_badge.setText("⚠️")
            self.status_badge.setStyleSheet("background: #FEE2E2; border-radius: 9px; font-size: 12px;")
            self.status_badge.setToolTip("未识别到金额，请手动修改")
            self.status_badge.show()
            # 未识别发票红色背景
            self.setStyleSheet("QWidget#ItemRow { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(254, 226, 226, 0.5), stop:1 rgba(254, 226, 226, 0.2)); border-left: 3px solid #DC2626; }")
        elif is_manually_edited:
            self.status_badge.setText("✓")
            self.status_badge.setStyleSheet("background: #D1FAE5; border-radius: 9px; font-size: 12px; color: #059669; font-weight: bold;")
            self.status_badge.setToolTip("已手动修改金额")
            self.status_badge.show()
            self.setStyleSheet("QWidget#ItemRow { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(209, 250, 229, 0.3), stop:1 rgba(209, 250, 229, 0.1)); border-left: 3px solid #10B981; }")
        else:
            self.status_badge.hide()
            self.setStyleSheet("")

class DynamicSplashScreen(QWidget):
    finished = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(500, 320)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 渐变背景卡片
        self.card = QFrame()
        self.card.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2563EB,
                    stop:1 #7C3AED
                );
                border-radius: 16px;
            }
        """)
        
        # 阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 8)
        self.card.setGraphicsEffect(shadow)
        main_layout.addWidget(self.card)
        
        # 卡片内容布局
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(40, 50, 40, 50)
        card_layout.setSpacing(20)
        
        # 应用名称
        title_lbl = QLabel(APP_NAME)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("""
            color: white;
            font-weight: 700;
            font-size: 28px;
            letter-spacing: 2px;
            background: transparent;
            border: none;
        """)
        card_layout.addWidget(title_lbl)
        
        # 版本号
        ver_lbl = QLabel(APP_VERSION)
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver_lbl.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8);
            font-size: 14px;
            background: transparent;
            border: none;
        """)
        card_layout.addWidget(ver_lbl)
        
        card_layout.addSpacing(10)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 255, 255, 0.8),
                    stop:1 rgba(255, 255, 255, 1)
                );
                border-radius: 3px;
            }
        """)
        card_layout.addWidget(self.progress)
        
        # 状态文字
        self.status_lbl = QLabel("正在初始化...")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 12px; background: transparent; border: none;")
        card_layout.addWidget(self.status_lbl)
        
        # 启动模拟加载计时器
        self.timer = self.startTimer(30)
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
            self.status_lbl.setText("正在配置环境...")
        elif self.step < 90:
            self.status_lbl.setText("即将进入系统...")
