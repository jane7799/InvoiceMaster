
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QProgressBar, QPushButton, QFrame, QLineEdit,
                           QMessageBox, QWidget, QGraphicsDropShadowEffect, QApplication)
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal
from src.utils.constants import APP_NAME, APP_VERSION, APP_AUTHOR_CN
from src.utils.icons import Icons
# Note: UI_CONFIG is not easily extractable yet, using default shadow values or passing them might be better.
# For now, sticking to hardcoded values or simplified logic.

class ProgressDialog(QDialog):
    """异步操作进度对话框"""
    cancelled = pyqtSignal()
    
    def __init__(self, parent, title="处理中", can_cancel=True):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(420, 180)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(15)
        
        # 标题标签
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: 600; color: #1E293B;")
        layout.addWidget(self.title_label)
        
        # 当前文件标签
        self.file_label = QLabel("准备中...")
        self.file_label.setStyleSheet("font-size: 13px; color: #64748B;")
        layout.addWidget(self.file_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 8px;
                background-color: #E2E8F0;
                height: 16px;
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #60A5FA, stop:0.5 #3B82F6, stop:1 #2563EB);
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        if can_cancel:
            self.cancel_btn = QPushButton("取消")
            self.cancel_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F1F5F9;
                    border: 1.5px solid #E2E8F0;
                    border-radius: 8px;
                    padding: 8px 24px;
                    color: #475569;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #E2E8F0;
                    border-color: #CBD5E1;
                }
            """)
            self.cancel_btn.clicked.connect(self._on_cancel)
            btn_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self._is_cancelled = False
        
    def _on_cancel(self):
        self._is_cancelled = True
        self.cancelled.emit()
        self.file_label.setText("正在取消...")
        self.cancel_btn.setEnabled(False)
        
    def update_progress(self, current, total, filename=""):
        percent = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(percent)
        self.file_label.setText(f"正在处理 ({current}/{total}): {filename}")
        QApplication.processEvents()
        
    def set_title(self, title):
        self.title_label.setText(title)
        
    def is_cancelled(self):
        return self._is_cancelled

class ActivationDialog(QDialog):
    """激活管理对话框"""
    def __init__(self, parent, license_manager):
        super().__init__(parent)
        self.license_manager = license_manager
        self.setWindowTitle("激活管理")
        self.resize(550, 520)
        self.setStyleSheet("""
            QDialog {
                background-color: #F8FAFC;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 渐变标题栏
        header = QWidget()
        header.setFixedHeight(100)
        header.setStyleSheet("""
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #2563EB,
                stop:1 #7C3AED
            );
            border-radius: 0px;
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(30, 20, 30, 20)
        header_layout.setSpacing(5)
        
        title = QLabel("🔑 Excel 导出功能激活")
        title.setStyleSheet("""
            font-size: 22px;
            font-weight: 700;
            color: white;
            background: transparent;
        """)
        header_layout.addWidget(title)
        
        subtitle = QLabel("管理您的软件授权和试用状态")
        subtitle.setStyleSheet("""
            font-size: 13px;
            color: rgba(255, 255, 255, 0.9);
            background: transparent;
        """)
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header)
        
        # 内容区域
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)
        
        # 激活状态卡片
        info = self.license_manager.get_activation_info()
        status_card = QFrame()
        status_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
            }
        """)
        
        status_shadow = QGraphicsDropShadowEffect()
        status_shadow.setBlurRadius(20)
        status_shadow.setColor(QColor(0, 0, 0, 30))
        status_shadow.setOffset(0, 2)
        status_card.setGraphicsEffect(status_shadow)
        
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(20, 20, 20, 20)
        status_layout.setSpacing(10)
        
        if info['is_activated']:
            status_text = "✅ 已激活"
            status_color = "#10B981"
            status_bg = "#ECFDF5"
        else:
            remaining = info['remaining_trials']
            status_text = f"⚠️ 未激活 (剩余试用: {remaining}/10次)"
            status_color = "#F59E0B"
            status_bg = "#FEF3C7"
        
        self.status_label = QLabel(status_text)
        self.status_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {status_color};
            padding: 12px 20px;
            background: {status_bg};
            border-radius: 8px;
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        content_layout.addWidget(status_card)
        
        # 机器码卡片
        machine_card = QFrame()
        machine_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
            }
        """)
        
        machine_shadow = QGraphicsDropShadowEffect()
        machine_shadow.setBlurRadius(20)
        machine_shadow.setColor(QColor(0, 0, 0, 30))
        machine_shadow.setOffset(0, 2)
        machine_card.setGraphicsEffect(machine_shadow)
        
        machine_layout = QVBoxLayout(machine_card)
        machine_layout.setContentsMargins(20, 20, 20, 20)
        machine_layout.setSpacing(12)
        
        machine_title = QLabel("📱 机器码")
        machine_title.setStyleSheet("""
            font-size: 15px;
            font-weight: 600;
            color: #1E293B;
        """)
        machine_layout.addWidget(machine_title)
        
        hint = QLabel("请将以下机器码发送给开发者以获取激活码")
        hint.setStyleSheet("""
            color: #64748B;
            font-size: 12px;
        """)
        machine_layout.addWidget(hint)
        
        machine_code_layout = QHBoxLayout()
        self.machine_code_edit = QLineEdit(self.license_manager.get_machine_code())
        self.machine_code_edit.setReadOnly(True)
        self.machine_code_edit.setStyleSheet("""
            font-family: 'Courier New', monospace;
            font-size: 15px;
            font-weight: 600;
            padding: 12px 16px;
            background: #F1F5F9;
            border: 2px solid #E2E8F0;
            border-radius: 8px;
            color: #1E293B;
        """)
        machine_code_layout.addWidget(self.machine_code_edit)
        
        copy_btn = QPushButton("📋 复制")
        copy_btn.setFixedWidth(90)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1.5px solid #CBD5E1;
                border-radius: 8px;
                padding: 12px 16px;
                font-weight: 500;
                color: #475569;
            }
            QPushButton:hover {
                background-color: #F8FAFC;
                border-color: #2563EB;
                color: #2563EB;
            }
        """)
        copy_btn.clicked.connect(self.copy_machine_code)
        machine_code_layout.addWidget(copy_btn)
        
        machine_layout.addLayout(machine_code_layout)
        content_layout.addWidget(machine_card)
        
        # 激活码卡片
        activation_card = QFrame()
        activation_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
            }
        """)
        
        activation_shadow = QGraphicsDropShadowEffect()
        activation_shadow.setBlurRadius(20)
        activation_shadow.setColor(QColor(0, 0, 0, 30))
        activation_shadow.setOffset(0, 2)
        activation_card.setGraphicsEffect(activation_shadow)
        
        activation_layout = QVBoxLayout(activation_card)
        activation_layout.setContentsMargins(20, 20, 20, 20)
        activation_layout.setSpacing(12)
        
        activation_title = QLabel("🔐 激活码")
        activation_title.setStyleSheet("""
            font-size: 15px;
            font-weight: 600;
            color: #1E293B;
        """)
        activation_layout.addWidget(activation_title)
        
        activation_hint = QLabel("请输入从开发者处获得的激活码")
        activation_hint.setStyleSheet("""
            color: #64748B;
            font-size: 12px;
        """)
        activation_layout.addWidget(activation_hint)
        
        self.activation_code_edit = QLineEdit()
        self.activation_code_edit.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        self.activation_code_edit.setStyleSheet("""
            font-family: 'Courier New', monospace;
            font-size: 15px;
            font-weight: 600;
            padding: 12px 16px;
            background: white;
            border: 2px solid #CBD5E1;
            border-radius: 8px;
            color: #1E293B;
        """)
        activation_layout.addWidget(self.activation_code_edit)
        
        content_layout.addWidget(activation_card)
        content_layout.addStretch()
        
        layout.addWidget(content)
        
        # 底部按钮区域
        button_container = QWidget()
        button_container.setStyleSheet("background-color: white; border-top: 1px solid #E2E8F0;")
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(30, 20, 30, 20)
        button_layout.setSpacing(12)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1.5px solid #CBD5E1;
                border-radius: 8px;
                padding: 10px 32px;
                font-weight: 500;
                color: #475569;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #F8FAFC;
                border-color: #2563EB;
                color: #2563EB;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addStretch()
        
        activate_btn = QPushButton("🔓 立即激活")
        activate_btn.setMinimumHeight(44)
        activate_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3B82F6, stop:1 #2563EB);
                border: none;
                color: white;
                font-weight: 600;
                font-size: 14px;
                border-radius: 8px;
                padding: 10px 32px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2563EB, stop:1 #1D4ED8);
            }
        """)
        activate_btn.clicked.connect(self.activate)
        button_layout.addWidget(activate_btn)
        
        layout.addWidget(button_container)
    
    def copy_machine_code(self):
        """复制机器码到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.machine_code_edit.text())
        QMessageBox.information(self, "成功", "机器码已复制到剪贴板！")
    
    def activate(self):
        """激活软件"""
        activation_code = self.activation_code_edit.text().strip()
        if not activation_code:
            QMessageBox.warning(self, "错误", "请输入激活码！")
            return
        
        if self.license_manager.activate(activation_code):
            QMessageBox.information(self, "成功", "激活成功！感谢您的支持！")
            self.accept()
        else:
            QMessageBox.critical(self, "失败", "激活码无效，请检查后重试！")

class AboutDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.resize(500, 520)
        self.setStyleSheet("""
            QDialog {
                background-color: #F8FAFC;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 渐变标题栏
        header = QWidget()
        header.setFixedHeight(100)
        header.setStyleSheet("""
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #2563EB,
                stop:1 #7C3AED
            );
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(30, 20, 30, 20)
        header_layout.setSpacing(5)
        
        title = QLabel(f"{APP_NAME}")
        title.setStyleSheet("""
            font-size: 22px;
            font-weight: 700;
            color: white;
            background: transparent;
        """)
        header_layout.addWidget(title)
        
        subtitle = QLabel(f"{APP_VERSION} · {APP_AUTHOR_CN}")
        subtitle.setStyleSheet("""
            font-size: 13px;
            color: rgba(255, 255, 255, 0.9);
            background: transparent;
        """)
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header)
        
        # 内容区域
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)
        
        # 说明文字卡片
        text_card = QFrame()
        text_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
            }
        """)
        
        text_shadow = QGraphicsDropShadowEffect()
        text_shadow.setBlurRadius(20)
        text_shadow.setColor(QColor(0, 0, 0, 30))
        text_shadow.setOffset(0, 2)
        text_card.setGraphicsEffect(text_shadow)
        
        text_layout = QVBoxLayout(text_card)
        text_layout.setContentsMargins(20, 20, 20, 20)
        text_layout.setSpacing(10)
        
        txt = QLabel("本软件不收集任何数据和隐私\n如果这个软件对你有帮助，不妨请我喝杯咖啡或奶茶。\n感谢你的认可与支持！")
        txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        txt.setWordWrap(True)
        txt.setStyleSheet("""
            color: #64748B;
            font-size: 13px;
            line-height: 24px;
        """)
        text_layout.addWidget(txt)
        
        content_layout.addWidget(text_card)
        
        # 二维码卡片 (简化版，无需 resource_path 复杂逻辑，由 main 传入或忽略)
        # For simplicity, bypassing QR code logic requiring resource_path for now inside this extracted class, 
        # or assuming resource_path is available from utils.
        # But resource_path was in InvoiceMaster.py.
        # I should move resource_path to src.utils.
        
        from src.utils.utils import resource_path
        
        qr_card = QFrame()
        qr_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
            }
        """)
        
        qr_shadow = QGraphicsDropShadowEffect()
        qr_shadow.setBlurRadius(20)
        qr_shadow.setColor(QColor(0, 0, 0, 30))
        qr_shadow.setOffset(0, 2)
        qr_card.setGraphicsEffect(qr_shadow)
        
        qr_layout = QHBoxLayout(qr_card)
        qr_layout.setContentsMargins(20, 20, 20, 20)
        qr_layout.setSpacing(30)
        qr_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        def make_qr(path, t, icon):
            real_path = resource_path(path)
            w = QWidget(); wl = QVBoxLayout(w); wl.setContentsMargins(0,0,0,0); wl.setSpacing(10); wl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            IMG_SIZE = 140; CONT_SIZE = IMG_SIZE + 10
            l = QLabel(); l.setFixedSize(CONT_SIZE, CONT_SIZE); l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.setStyleSheet("background:white; border:1px solid #ddd; border-radius:8px")
            if os.path.exists(real_path): l.setPixmap(QPixmap(real_path).scaled(IMG_SIZE, IMG_SIZE, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else: l.setText(t); l.setStyleSheet(f"background:#f0f0f0; border:1px solid #ccc; border-radius:8px; color:#999; font-size:14px; qproperty-alignment: AlignCenter;")
            tl = QLabel(t); tl.setAlignment(Qt.AlignmentFlag.AlignCenter); tl.setStyleSheet("color:#333; font-size:14px; font-weight:bold;")
            wl.addWidget(l); wl.addWidget(tl); return w
        
        qr_layout.addWidget(make_qr("qr1.jpg", "打赏", "💰")); qr_layout.addWidget(make_qr("qr2.jpg", "加好友", "👋"))
        
        content_layout.addWidget(qr_card)
        layout.addWidget(content)
