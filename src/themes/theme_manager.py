"""
主题管理模块
提供 Light/Dark 主题样式
"""

class ThemeManager:
    """主题管理器"""
    
    SCROLLBAR_CSS = """
        QScrollBar:vertical {
            border: none;
            background: transparent;
            width: 10px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: rgba(0, 0, 0, 0.2);
            min-height: 30px;
            border-radius: 5px;
            margin: 2px;
        }
        QScrollBar::handle:vertical:hover {
            background: rgba(0, 0, 0, 0.3);
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar:horizontal {
            border: none;
            background: transparent;
            height: 10px;
            margin: 0px;
        }
        QScrollBar::handle:horizontal {
            background: rgba(0, 0, 0, 0.2);
            min-width: 30px;
            border-radius: 5px;
            margin: 2px;
        }
        QScrollBar::handle:horizontal:hover {
            background: rgba(0, 0, 0, 0.3);
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
    """
    
    COMMON_CSS = """
        QRadioButton {
            color: #475569;
            font-weight: 500;
            font-size: 13px;
            spacing: 8px;
        }
        QCheckBox {
            color: #475569;
            font-weight: 500;
            font-size: 13px;
            spacing: 8px;
        }
        QWidget#ItemRow {
            background: transparent;
            border-radius: 10px;
        }
        QLabel#ItemTitle {
            font-weight: 600;
            font-size: 13px;
            color: #1E293B;
        }
        QLabel#ItemDetail {
            color: #64748B;
            font-size: 12px;
        }
        QPushButton#RowDelBtn {
            background: transparent;
            border: none;
            border-radius: 6px;
        }
        QPushButton#RowDelBtn:hover {
            background-color: #FEE2E2;
        }
        
        QToolButton#LayoutCard {
            background-color: white;
            border: 2px solid #E2E8F0;
            border-radius: 16px;
            padding: 6px;
        }
        QToolButton#LayoutCard:hover {
            border-color: #60A5FA;
            background-color: #F0F9FF;
        }
        QToolButton#LayoutCard:checked {
            border: 3px solid #2563EB;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #DBEAFE, stop:1 #EFF6FF);
        }
        QFrame#PreviewControlBar {
            background-color: white;
            border-top: 1px solid #E2E8F0;
            border-radius: 0px 0px 12px 12px;
        }
        QLabel#PageLabel {
            font-size: 12px;
            color: #64748B;
        }
        QLabel#Title {
            font-size: 15px;
            font-weight: 600;
            color: #1E293B;
        }
    """

    CSS_LIGHT = """
    QMainWindow {
        background-color: #F8FAFC;
    }
    QWidget {
        color: #1E293B;
        font-family: "PingFang SC", "Microsoft YaHei UI", "Segoe UI", sans-serif;
        font-size: 13px;
    }
    QFrame#Card {
        background-color: white;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
    }
    QPushButton {
        background-color: white;
        border: 1.5px solid #E2E8F0;
        border-radius: 10px;
        padding: 10px 18px;
        font-weight: 500;
        color: #475569;
    }
    QPushButton:hover {
        background-color: #F8FAFC;
        border-color: #3B82F6;
        color: #2563EB;
    }
    QPushButton:pressed {
        background-color: #EFF6FF;
    }
    QPushButton#IconBtn {
        background: transparent;
        border: none;
        border-radius: 8px;
        padding: 8px;
    }
    QPushButton#IconBtn:hover {
        background-color: #F1F5F9;
    }
    QPushButton#PrimaryBtn {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #60A5FA, stop:0.5 #3B82F6, stop:1 #2563EB);
        border: none;
        color: white;
        font-weight: 600;
        font-size: 14px;
        border-radius: 12px;
        padding: 12px 24px;
    }
    QPushButton#PrimaryBtn:hover {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #3B82F6, stop:0.5 #2563EB, stop:1 #1D4ED8);
    }
    QPushButton#DangerBtn {
        color: #DC2626;
    }
    QPushButton#PropBtn {
        color: #475569;
        border: 1.5px solid #E2E8F0;
        border-radius: 8px;
    }
    QListWidget {
        background-color: white;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        outline: none;
        padding: 6px;
    }
    QListWidget::item {
        border-bottom: 1px solid #F1F5F9;
        border-radius: 8px;
        margin: 3px 2px;
        padding: 2px;
    }
    QListWidget::item:selected {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #DBEAFE, stop:1 #EFF6FF);
        border-left: 4px solid #2563EB;
        color: #1E293B;
    }
    QListWidget::item:hover {
        background-color: #F8FAFC;
        border-left: 3px solid #60A5FA;
    }
    QLineEdit, QComboBox, QSpinBox {
        border: 1.5px solid #E2E8F0;
        border-radius: 10px;
        padding: 10px 14px;
        background: white;
        min-height: 22px;
        font-size: 13px;
    }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
        border-color: #3B82F6;
        background: #FEFEFE;
    }
    QComboBox::drop-down {
        border: none;
        width: 28px;
    }
    QComboBox::down-arrow {
        width: 12px;
        height: 12px;
    }
    QGroupBox {
        border: none;
        font-weight: 600;
        margin-top: 12px;
        color: #1E293B;
    }
    """ + SCROLLBAR_CSS + COMMON_CSS
    
    CSS_DARK = """
    QMainWindow {
        background-color: #0F172A;
    }
    QWidget {
        color: #E2E8F0;
        font-family: "Microsoft YaHei UI", sans-serif;
        font-size: 13px;
    }
    QFrame#Card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 16px;
    }
    QPushButton {
        background-color: #1E293B;
        border: 1.5px solid #475569;
        border-radius: 10px;
        padding: 10px 18px;
        color: #E2E8F0;
        font-weight: 500;
    }
    QPushButton:hover {
        background-color: #334155;
        border-color: #3B82F6;
        color: white;
    }
    QPushButton#IconBtn {
        background: transparent;
        border: none;
        border-radius: 8px;
    }
    QPushButton#IconBtn:hover {
        background-color: #334155;
    }
    QPushButton#PrimaryBtn {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #60A5FA, stop:0.5 #3B82F6, stop:1 #2563EB);
        border: none;
        color: white;
        font-weight: 600;
        border-radius: 12px;
        padding: 12px 24px;
    }
    QPushButton#DangerBtn {
        color: #EF4444;
    }
    QListWidget {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        outline: none;
        padding: 6px;
    }
    QListWidget::item {
        border-bottom: 1px solid #334155;
        border-radius: 8px;
        margin: 3px 2px;
    }
    QListWidget::item:selected {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #1E40AF, stop:1 #1E3A8A);
        border-left: 4px solid #3B82F6;
        color: white;
    }
    QListWidget::item:hover {
        background-color: #334155;
        border-left: 3px solid #60A5FA;
    }
    QLineEdit, QComboBox, QSpinBox {
        border: 1.5px solid #475569;
        border-radius: 10px;
        padding: 10px 14px;
        background: #1E293B;
        color: white;
    }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
        border-color: #3B82F6;
    }
    QRadioButton {
        color: #E2E8F0;
    }
    QCheckBox {
        color: #E2E8F0;
    }
    QLabel#ItemTitle {
        color: #F1F5F9;
    }
    QLabel#ItemDetail {
        color: #94A3B8;
    }
    QToolButton#LayoutCard {
        background-color: #1E293B;
        border: 2px solid #475569;
        border-radius: 16px;
    }
    QToolButton#LayoutCard:hover {
        border-color: #60A5FA;
        background-color: #334155;
    }
    QToolButton#LayoutCard:checked {
        border-color: #3B82F6;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #1E40AF, stop:1 #1E3A8A);
    }
    QFrame#PreviewControlBar {
        background-color: #1E293B;
        border-top: 1px solid #334155;
    }
    QLabel#PageLabel {
        color: #94A3B8;
    }
    QLabel#Title {
        color: #F1F5F9;
    }
    QGroupBox {
        border: none;
        font-weight: 600;
        margin-top: 12px;
        color: #E2E8F0;
    }
    QDialog {
        background-color: #1E293B;
        color: #E2E8F0;
    }
    QMessageBox {
        background-color: #1E293B;
    }
    QMessageBox QLabel {
        color: #E2E8F0;
    }
    QInputDialog {
        background-color: #1E293B;
    }
    QProgressBar {
        border: 1px solid #475569;
        border-radius: 8px;
        background-color: #334155;
        text-align: center;
        color: white;
    }
    QProgressBar::chunk {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #3B82F6, stop:1 #60A5FA);
        border-radius: 7px;
    }
    QToolTip {
        background-color: #334155;
        color: #F1F5F9;
        border: 1px solid #475569;
        border-radius: 6px;
        padding: 6px 10px;
    }
    QScrollBar:vertical {
        background: #1E293B;
    }
    QScrollBar::handle:vertical {
        background: #475569;
    }
    QScrollBar::handle:vertical:hover {
        background: #64748B;
    }
    QScrollBar:horizontal {
        background: #1E293B;
    }
    QScrollBar::handle:horizontal {
        background: #475569;
    }
    QScrollBar::handle:horizontal:hover {
        background: #64748B;
    }
    """ + SCROLLBAR_CSS

    @staticmethod
    def apply(app, mode="Light"):
        """应用主题到应用程序"""
        if mode == "Auto":
            mode = "Light"
        if mode == "Dark":
            app.setStyleSheet(ThemeManager.CSS_DARK)
            return "#ffffff"
        else:
            app.setStyleSheet(ThemeManager.CSS_LIGHT)
            return "#555555"
