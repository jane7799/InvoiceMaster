
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QScrollArea, QFrame, QPushButton)
from PyQt6.QtCore import Qt, QPointF, QTimer
from PyQt6.QtGui import QPixmap, QImage, QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from src.utils.icons import Icons

class HandScrollArea(QScrollArea):
    def __init__(self, parent_widget):
        super().__init__()
        self.parent_widget = parent_widget 
        self.setWidgetResizable(True)
        self.setStyleSheet("background-color: #525659; border: none;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.is_panning = False; self.last_mouse_pos = QPointF()
        self.enable_interaction = True
    def set_interactive(self, enable):
        self.enable_interaction = enable
        self.setCursor(Qt.CursorShape.OpenHandCursor if enable else Qt.CursorShape.ArrowCursor)
    def wheelEvent(self, event):
        if self.enable_interaction and event.modifiers() == Qt.KeyboardModifier.ControlModifier and self.parent_widget:
            delta = event.angleDelta().y(); 
            if delta > 0: self.parent_widget.zoom_in()
            else: self.parent_widget.zoom_out()
            event.accept()
        else: super().wheelEvent(event)
    def mousePressEvent(self, event):
        if self.enable_interaction and event.button() == Qt.MouseButton.LeftButton:
            self.is_panning = True; self.last_mouse_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor); event.accept()
        else: super().mousePressEvent(event)
    def mouseReleaseEvent(self, event):
        if self.enable_interaction and event.button() == Qt.MouseButton.LeftButton:
            self.is_panning = False; self.setCursor(Qt.CursorShape.OpenHandCursor); event.accept()
        else: super().mouseReleaseEvent(event)
    def mouseMoveEvent(self, event):
        if self.enable_interaction and self.is_panning:
            delta = event.position() - self.last_mouse_pos
            self.last_mouse_pos = event.position()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(delta.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(delta.y()))
            event.accept()
        else: super().mouseMoveEvent(event)

class AdvancedPreviewArea(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self); self.layout.setContentsMargins(0,0,0,0); self.layout.setSpacing(0)
        self.scroll_area = HandScrollArea(self)
        self.scroll_area.set_interactive(False)
        self.container = QWidget(); self.container.setStyleSheet("background-color: transparent;")
        self.scroll_layout = QVBoxLayout(self.container); self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setSpacing(30); self.scroll_layout.setContentsMargins(20, 20, 20, 20)
        self.scroll_area.setWidget(self.container)
        self.placeholder = QLabel("💡 暂无内容 - 请在左侧添加发票")
        self.placeholder.setStyleSheet("color: #aaa; font-size: 16px; font-weight: bold;")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_layout.addWidget(self.placeholder)
        self.control_bar = QFrame(); self.control_bar.setObjectName("PreviewControlBar"); self.control_bar.setFixedHeight(45)
        cb_layout = QHBoxLayout(self.control_bar); cb_layout.setContentsMargins(15, 5, 15, 5)
        self.btn_prev = QPushButton(); self.btn_prev.setIcon(Icons.get("prev")); self.btn_prev.setObjectName("IconBtn"); self.btn_prev.setToolTip("上一页"); self.btn_prev.clicked.connect(self.scroll_prev)
        self.lbl_page = QLabel("0 张"); self.lbl_page.setObjectName("PageLabel")
        self.btn_next = QPushButton(); self.btn_next.setIcon(Icons.get("next")); self.btn_next.setObjectName("IconBtn"); self.btn_next.setToolTip("下一页"); self.btn_next.clicked.connect(self.scroll_next)
        cb_layout.addWidget(self.btn_prev); cb_layout.addWidget(self.lbl_page); cb_layout.addWidget(self.btn_next)
        cb_layout.addStretch()
        self.layout.addWidget(self.scroll_area, 1); self.layout.addWidget(self.control_bar)
        self.raw_page_images = []; self.scale_factor = 1.0; self.page_widgets = []
        self.control_bar.setVisible(True)
        self.hq_timer = QTimer(); self.hq_timer.setSingleShot(True); self.hq_timer.timeout.connect(lambda: self.render_pages(True))

    def show_pages(self, page_images):
        self.raw_page_images = page_images; self.render_pages()
        self.lbl_page.setText(f"共 {len(page_images)} 页")

    def render_pages(self, high_quality=True):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if not self.raw_page_images: self.scroll_layout.addWidget(self.placeholder); return
        for i, img in enumerate(self.raw_page_images):
            page_lbl = QLabel(); pix = QPixmap.fromImage(img)
            view_width = self.scroll_area.viewport().width() - 60
            if view_width < 300: view_width = 300
            # 始终使用高质量渲染，避免滚动时模糊
            scaled_pix = pix.scaledToWidth(view_width, Qt.TransformationMode.SmoothTransformation)
            page_lbl.setPixmap(scaled_pix)
            shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(25); shadow.setColor(QColor(0,0,0,120)); shadow.setOffset(0, 8)
            page_lbl.setGraphicsEffect(shadow)
            page_container = QWidget(); pc_layout = QVBoxLayout(page_container); pc_layout.setContentsMargins(0,0,0,0); pc_layout.setSpacing(5)
            pc_layout.addWidget(page_lbl, 0, Qt.AlignmentFlag.AlignCenter)
            num_lbl = QLabel(f"- {i+1} -"); num_lbl.setStyleSheet("color:#888; font-size:11px;"); num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pc_layout.addWidget(num_lbl)
            self.scroll_layout.addWidget(page_container)

    def trigger_update(self): self.render_pages(False); self.hq_timer.start(500)
    def scroll_prev(self): self.scroll_area.verticalScrollBar().setValue(max(0, self.scroll_area.verticalScrollBar().value() - 600)); self.trigger_update()
    def scroll_next(self): sb=self.scroll_area.verticalScrollBar(); sb.setValue(min(sb.maximum(), sb.value() + 600)); self.trigger_update()
    def zoom_in(self): pass
    def zoom_out(self): pass
    def resizeEvent(self, e): 
        if self.raw_page_images: self.render_pages()
        super().resizeEvent(e)

class SingleDocViewer(HandScrollArea):
    def __init__(self):
        super().__init__(None) 
        self.set_interactive(True) 
        self.label = QLabel(""); self.label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.setWidget(self.label)
        self.current_pixmap = None; self.zoom_level = 1.0
        self.hq_timer = QTimer(); self.hq_timer.setSingleShot(True); self.hq_timer.timeout.connect(lambda: self.refresh_view(True))

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0: self.zoom_in()
            else: self.zoom_out()
            event.accept()
        else: super().wheelEvent(event)
    def zoom_in(self): self.zoom_level *= 1.1; self.refresh_view(False); self.hq_timer.start(500)
    def zoom_out(self): self.zoom_level /= 1.1; self.refresh_view(False); self.hq_timer.start(500)
    def set_image(self, img_or_path):
        if isinstance(img_or_path, QImage): self.current_pixmap = QPixmap.fromImage(img_or_path)
        elif isinstance(img_or_path, str) and os.path.exists(img_or_path): self.current_pixmap = QPixmap(img_or_path)
        self.fit_to_window()
    def show_result(self, img): self.set_image(img)
    def fit_to_window(self):
        if not self.current_pixmap: return
        view_size = self.viewport().size()
        w_ratio = (view_size.width() - 40) / self.current_pixmap.width()
        h_ratio = (view_size.height() - 40) / self.current_pixmap.height()
        self.zoom_level = min(w_ratio, h_ratio)
        self.refresh_view(True)
    def refresh_view(self, high_quality=True):
        if not self.current_pixmap: return
        target_w = int(self.current_pixmap.width() * self.zoom_level)
        target_h = int(self.current_pixmap.height() * self.zoom_level)
        # 始终使用高质量渲染
        scaled_pix = self.current_pixmap.scaled(target_w, target_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.label.setPixmap(scaled_pix)
        shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(30); shadow.setColor(QColor(0,0,0,180)); shadow.setOffset(0, 10)
        self.label.setGraphicsEffect(shadow)
