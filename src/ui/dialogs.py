
import os
import time
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
    """异步操作进度对话框 [V3.6 增强版]
    
    新增功能：
    - 预计剩余时间
    - 处理速度（件/秒）
    - 成功/失败计数
    - 当前文件名显示
    """
    cancelled = pyqtSignal()
    
    def __init__(self, parent, title="处理中", can_cancel=True):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(480, 240)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(12)
        
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
        
        # 详细统计信息行
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        # 进度数
        self.count_label = QLabel("0/0")
        self.count_label.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 500;")
        stats_layout.addWidget(self.count_label)
        
        # 成功/失败计数
        self.result_label = QLabel("✅ 0  ❌ 0")
        self.result_label.setStyleSheet("font-size: 12px; color: #64748B;")
        stats_layout.addWidget(self.result_label)
        
        stats_layout.addStretch()
        
        # 处理速度
        self.speed_label = QLabel("")
        self.speed_label.setStyleSheet("font-size: 12px; color: #64748B;")
        stats_layout.addWidget(self.speed_label)
        
        # 预计剩余时间
        self.eta_label = QLabel("")
        self.eta_label.setStyleSheet("font-size: 12px; color: #3B82F6; font-weight: 500;")
        stats_layout.addWidget(self.eta_label)
        
        layout.addLayout(stats_layout)
        
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
        self._start_time = time.time()
        self._success_count = 0
        self._error_count = 0
        
    def _on_cancel(self):
        self._is_cancelled = True
        self.cancelled.emit()
        self.file_label.setText("正在取消...")
        self.cancel_btn.setEnabled(False)
        
    def update_progress(self, current, total, filename=""):
        """更新进度（增强版）"""
        percent = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(percent)
        
        # 文件名（截断过长的文件名）
        display_name = filename[:35] + "..." if len(filename) > 38 else filename
        self.file_label.setText(f"正在处理: {display_name}")
        
        # 进度数
        self.count_label.setText(f"{current}/{total}")
        
        # 计算速度和预计剩余时间
        elapsed = time.time() - self._start_time
        if elapsed > 0 and current > 0:
            speed = current / elapsed
            self.speed_label.setText(f"⚡ {speed:.1f} 件/秒")
            
            remaining = total - current
            if speed > 0:
                eta_seconds = remaining / speed
                if eta_seconds < 60:
                    self.eta_label.setText(f"⏱️ 约 {int(eta_seconds)} 秒")
                else:
                    self.eta_label.setText(f"⏱️ 约 {int(eta_seconds/60)} 分钟")
            else:
                self.eta_label.setText("")
        
        # 更新成功/失败计数
        self.result_label.setText(f"✅ {self._success_count}  ❌ {self._error_count}")
        
        QApplication.processEvents()
    
    def record_success(self):
        """记录成功处理"""
        self._success_count += 1
        self.result_label.setText(f"✅ {self._success_count}  ❌ {self._error_count}")
        
    def record_error(self):
        """记录处理失败"""
        self._error_count += 1
        self.result_label.setText(f"✅ {self._success_count}  ❌ {self._error_count}")
        
    def set_title(self, title):
        self.title_label.setText(title)
        
    def is_cancelled(self):
        return self._is_cancelled
    
    def get_statistics(self):
        """获取处理统计"""
        elapsed = time.time() - self._start_time
        return {
            "success": self._success_count,
            "error": self._error_count,
            "elapsed_seconds": elapsed,
            "speed": (self._success_count + self._error_count) / elapsed if elapsed > 0 else 0
        }

# ActivationDialog 已移除，激活功能不再需要


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
