
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QWidget, QFrame, QLineEdit, QPushButton, QComboBox, 
                           QGraphicsDropShadowEffect, QMessageBox)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QSettings
# 激活功能已移除
from src.utils.icons import Icons

class SettingsDlg(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.resize(550, 420)
        self.setStyleSheet("""
            QDialog {
                background-color: #F8FAFC;
            }
        """)
        self.parent = parent
        s = QSettings("MySoft", "InvoiceMaster")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 渐变标题栏
        header = QWidget()
        header.setFixedHeight(90)
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
        
        title = QLabel("⚙️ 应用设置")
        title.setStyleSheet("""
            font-size: 22px;
            font-weight: 700;
            color: white;
            background: transparent;
        """)
        header_layout.addWidget(title)
        
        subtitle = QLabel("配置主题和 API 密钥")
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
        
        # 激活功能已移除
        
        # 主题设置卡片
        theme_card = QFrame()
        theme_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
            }
        """)
        
        theme_shadow = QGraphicsDropShadowEffect()
        theme_shadow.setBlurRadius(20)
        theme_shadow.setColor(QColor(0, 0, 0, 30))
        theme_shadow.setOffset(0, 2)
        theme_card.setGraphicsEffect(theme_shadow)
        
        theme_layout = QVBoxLayout(theme_card)
        theme_layout.setContentsMargins(20, 20, 20, 20)
        theme_layout.setSpacing(15)
        
        theme_title = QLabel("🎨 外观主题")
        theme_title.setStyleSheet("""
            font-size: 15px;
            font-weight: 600;
            color: #1E293B;
        """)
        theme_layout.addWidget(theme_title)
        
        self.cb_th = QComboBox()
        self.cb_th.addItems(["Light", "Dark"])
        self.cb_th.setCurrentText(s.value("theme", "Light"))
        self.cb_th.setStyleSheet("""
            QComboBox {
                padding: 10px 12px;
                border: 2px solid #CBD5E1;
                border-radius: 8px;
                background: white;
                font-size: 14px;
            }
            QComboBox:focus {
                border-color: #2563EB;
            }
        """)
        self.cb_th.currentTextChanged.connect(parent.change_theme)
        theme_layout.addWidget(self.cb_th)
        
        content_layout.addWidget(theme_card)
        
        # API配置卡片
        api_card = QFrame()
        api_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
            }
        """)
        
        api_shadow = QGraphicsDropShadowEffect()
        api_shadow.setBlurRadius(20)
        api_shadow.setColor(QColor(0, 0, 0, 30))
        api_shadow.setOffset(0, 2)
        api_card.setGraphicsEffect(api_shadow)
        
        api_layout = QVBoxLayout(api_card)
        api_layout.setContentsMargins(20, 20, 20, 20)
        api_layout.setSpacing(15)
        
        api_title = QLabel("🔐 百度 OCR API 配置")
        api_title.setStyleSheet("""
            font-size: 15px;
            font-weight: 600;
            color: #1E293B;
        """)
        api_layout.addWidget(api_title)
        
        link = QLabel('<a href="https://console.bce.baidu.com">点击申请百度OCR Key (免费)</a>')
        link.setOpenExternalLinks(True)
        link.setStyleSheet("color: #2563EB; font-size: 12px;")
        api_layout.addWidget(link)
        
        self.ak = QLineEdit(s.value("ak", ""))
        self.ak.setPlaceholderText("API Key")
        self.ak.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 2px solid #CBD5E1;
                border-radius: 8px;
                background: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #2563EB;
            }
        """)
        api_layout.addWidget(self.ak)
        
        self.sk = QLineEdit(s.value("sk", ""))
        self.sk.setEchoMode(QLineEdit.EchoMode.Password)
        self.sk.setPlaceholderText("Secret Key")
        self.sk.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 2px solid #CBD5E1;
                border-radius: 8px;
                background: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #2563EB;
            }
        """)
        api_layout.addWidget(self.sk)
        
        content_layout.addWidget(api_card)
        
        # 私有OCR配置卡片
        private_ocr_card = QFrame()
        private_ocr_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
            }
        """)
        
        private_ocr_shadow = QGraphicsDropShadowEffect()
        private_ocr_shadow.setBlurRadius(20)
        private_ocr_shadow.setColor(QColor(0, 0, 0, 30))
        private_ocr_shadow.setOffset(0, 2)
        private_ocr_card.setGraphicsEffect(private_ocr_shadow)
        
        private_ocr_layout = QVBoxLayout(private_ocr_card)
        private_ocr_layout.setContentsMargins(20, 20, 20, 20)
        private_ocr_layout.setSpacing(15)
        
        private_ocr_title = QLabel("🏠 私有 OCR 服务（可选）")
        private_ocr_title.setStyleSheet("""
            font-size: 15px;
            font-weight: 600;
            color: #1E293B;
        """)
        private_ocr_layout.addWidget(private_ocr_title)
        
        private_ocr_hint = QLabel("配置后优先使用私有服务，失败时自动回退到百度OCR")
        private_ocr_hint.setStyleSheet("color: #64748B; font-size: 12px;")
        private_ocr_layout.addWidget(private_ocr_hint)
        
        self.private_ocr_url = QLineEdit(s.value("private_ocr_url", ""))
        self.private_ocr_url.setPlaceholderText("例如: http://192.168.1.4:8891 或 http://xxx.cpolar.top")
        self.private_ocr_url.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 2px solid #CBD5E1;
                border-radius: 8px;
                background: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #10B981;
            }
        """)
        private_ocr_layout.addWidget(self.private_ocr_url)
        
        content_layout.addWidget(private_ocr_card)
        content_layout.addStretch()
        
        layout.addWidget(content)
        
        # 底部按钮区域
        button_container = QWidget()
        button_container.setStyleSheet("background-color: white; border-top: 1px solid #E2E8F0;")
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(30, 20, 30, 20)
        button_layout.setSpacing(12)
        
        button_layout.addStretch()
        
        save_btn = QPushButton("💾 保存配置")
        save_btn.setMinimumHeight(44)
        save_btn.setStyleSheet("""
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
        save_btn.clicked.connect(self.save)
        button_layout.addWidget(save_btn)
        
        layout.addWidget(button_container)
    
    # 激活功能已移除
    
    def save(self):
        s = QSettings("MySoft", "InvoiceMaster")
        s.setValue("ak", self.ak.text())
        s.setValue("sk", self.sk.text())
        s.setValue("private_ocr_url", self.private_ocr_url.text().strip().rstrip('/'))
        s.setValue("theme", self.cb_th.currentText())
        self.accept()
