
class ThemeManager:
    SCROLLBAR_CSS = """
        QScrollBar:vertical {
            border: none;
            background: transparent;
            width: 8px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: rgba(0, 0, 0, 0.15);
            min-height: 40px;
            border-radius: 4px;
            margin: 2px;
        }
        QScrollBar::handle:vertical:hover {
            background: rgba(0, 0, 0, 0.25);
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar:horizontal {
            border: none;
            background: transparent;
            height: 8px;
            margin: 0px;
        }
        QScrollBar::handle:horizontal {
            background: rgba(0, 0, 0, 0.15);
            min-width: 40px;
            border-radius: 4px;
            margin: 2px;
        }
        QScrollBar::handle:horizontal:hover {
            background: rgba(0, 0, 0, 0.25);
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
        QRadioButton::indicator {
            width: 16px; height: 16px;
            border: 2px solid #CBD5E1;
            border-radius: 9px;
            background: white;
        }
        QRadioButton::indicator:checked {
            border: 2px solid #2563EB;
            background: qradialgradient(cx:0.5, cy:0.5, radius:0.4, fx:0.5, fy:0.5, stop:0 #2563EB, stop:1 #2563EB);
        }
        QCheckBox {
            color: #475569;
            font-weight: 500;
            font-size: 13px;
            spacing: 8px;
        }
        QCheckBox::indicator {
            width: 18px; height: 18px;
            border: 2px solid #CBD5E1;
            border-radius: 4px;
            background: white;
        }
        QCheckBox::indicator:checked {
            background: #2563EB;
            border-color: #2563EB;
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
            border-radius: 14px;
            padding: 6px;
        }
        QToolButton#LayoutCard:hover {
            border-color: #93C5FD;
            background-color: #EFF6FF;
        }
        QToolButton#LayoutCard:checked {
            border: 2.5px solid #2563EB;
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
        QLabel#SectionTitle {
            font-size: 13px;
            font-weight: 600;
            color: #64748B;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        QLabel#AppBarTitle {
            font-size: 16px;
            font-weight: 700;
            color: #0F172A;
        }
        QLabel#AppBarVersion {
            font-size: 11px;
            font-weight: 500;
            color: #94A3B8;
        }
        QLabel#StatsValue {
            font-size: 24px;
            font-weight: 700;
        }
        QLabel#StatsLabel {
            font-size: 11px;
            font-weight: 500;
            color: #94A3B8;
        }
    """

    CSS_LIGHT = """
    QMainWindow {
        background-color: #F1F5F9;
    }
    QWidget {
        color: #1E293B;
        font-family: "PingFang SC", "Microsoft YaHei UI", "Segoe UI", "Noto Sans SC", sans-serif;
        font-size: 13px;
    }
    QFrame#Card {
        background-color: white;
        border: 1px solid rgba(226, 232, 240, 0.8);
        border-radius: 16px;
    }
    QFrame#GlassCard {
        background-color: rgba(255, 255, 255, 0.85);
        border: 1px solid rgba(226, 232, 240, 0.6);
        border-radius: 16px;
    }
    QFrame#AppBar {
        background-color: rgba(255, 255, 255, 0.9);
        border: none;
        border-bottom: 1px solid rgba(226, 232, 240, 0.6);
        border-radius: 0px;
    }
    QFrame#StatsCard {
        background-color: white;
        border: 1px solid rgba(226, 232, 240, 0.8);
        border-radius: 14px;
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
        border-color: #93C5FD;
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
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #3B82F6, stop:1 #2563EB);
        border: none;
        color: white;
        font-weight: 600;
        font-size: 14px;
        border-radius: 12px;
        padding: 12px 24px;
    }
    QPushButton#PrimaryBtn:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #2563EB, stop:1 #1D4ED8);
    }
    QPushButton#PrimaryBtn:pressed {
        background: #1D4ED8;
    }
    QPushButton#DangerBtn {
        color: #DC2626;
        border-color: #FECACA;
        background-color: #FFF5F5;
    }
    QPushButton#DangerBtn:hover {
        background-color: #FEE2E2;
        border-color: #F87171;
    }
    QPushButton#ActionBtn {
        background: white;
        border: 1.5px solid #E2E8F0;
        border-radius: 10px;
        padding: 8px 16px;
        font-weight: 500;
        color: #475569;
        font-size: 13px;
    }
    QPushButton#ActionBtn:hover {
        background-color: #F8FAFC;
        border-color: #93C5FD;
        color: #2563EB;
    }
    QPushButton#PropBtn {
        color: #475569;
        border: 1.5px solid #E2E8F0;
        border-radius: 8px;
    }
    QListWidget {
        background-color: white;
        border: 1px solid rgba(226, 232, 240, 0.8);
        border-radius: 12px;
        outline: none;
        padding: 4px;
    }
    QListWidget::item {
        border-bottom: none;
        border-radius: 8px;
        margin: 2px 2px;
        padding: 2px;
    }
    QListWidget::item:selected {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #DBEAFE, stop:1 #EFF6FF);
        border-left: 3px solid #2563EB;
        color: #1E293B;
    }
    QListWidget::item:hover:!selected {
        background-color: #F8FAFC;
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
        border-color: #93C5FD;
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
    QComboBox QAbstractItemView {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        selection-background-color: #EFF6FF;
        selection-color: #1E293B;
        padding: 4px;
    }
    QGroupBox {
        border: none;
        font-weight: 600;
        margin-top: 12px;
        color: #1E293B;
    }
    QToolTip {
        background-color: #1E293B;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }
    """ + SCROLLBAR_CSS + COMMON_CSS
    
    CSS_DARK = """
    QMainWindow {
        background-color: #0B1120;
    }
    QWidget {
        color: #E2E8F0;
        font-family: "PingFang SC", "Microsoft YaHei UI", "Segoe UI", "Noto Sans SC", sans-serif;
        font-size: 13px;
    }
    QFrame#Card {
        background-color: #1E293B;
        border: 1px solid rgba(51, 65, 85, 0.6);
        border-radius: 16px;
    }
    QFrame#GlassCard {
        background-color: rgba(30, 41, 59, 0.85);
        border: 1px solid rgba(51, 65, 85, 0.4);
        border-radius: 16px;
    }
    QFrame#AppBar {
        background-color: rgba(15, 23, 42, 0.9);
        border: none;
        border-bottom: 1px solid rgba(51, 65, 85, 0.6);
        border-radius: 0px;
    }
    QFrame#StatsCard {
        background-color: #1E293B;
        border: 1px solid rgba(51, 65, 85, 0.6);
        border-radius: 14px;
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
        border-color: #60A5FA;
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
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #3B82F6, stop:1 #2563EB);
        border: none;
        color: white;
        font-weight: 600;
        border-radius: 12px;
        padding: 12px 24px;
    }
    QPushButton#PrimaryBtn:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #60A5FA, stop:1 #3B82F6);
    }
    QPushButton#DangerBtn {
        color: #EF4444;
        border-color: #7F1D1D;
        background-color: #1C1917;
    }
    QPushButton#DangerBtn:hover {
        background-color: #2D1B1B;
        border-color: #EF4444;
    }
    QPushButton#ActionBtn {
        background: #1E293B;
        border: 1.5px solid #475569;
        border-radius: 10px;
        padding: 8px 16px;
        font-weight: 500;
        color: #E2E8F0;
        font-size: 13px;
    }
    QPushButton#ActionBtn:hover {
        background-color: #334155;
        border-color: #60A5FA;
        color: white;
    }
    QListWidget {
        background-color: #1E293B;
        border: 1px solid rgba(51, 65, 85, 0.6);
        border-radius: 12px;
        outline: none;
        padding: 4px;
    }
    QListWidget::item {
        border-bottom: none;
        border-radius: 8px;
        margin: 2px 2px;
    }
    QListWidget::item:selected {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #1E3A8A, stop:1 #1E293B);
        border-left: 3px solid #3B82F6;
        color: white;
    }
    QListWidget::item:hover:!selected {
        background-color: #334155;
    }
    QLineEdit, QComboBox, QSpinBox {
        border: 1.5px solid #475569;
        border-radius: 10px;
        padding: 10px 14px;
        background: #1E293B;
        color: white;
    }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
        border-color: #60A5FA;
    }
    QComboBox QAbstractItemView {
        background: #1E293B;
        border: 1px solid #475569;
        border-radius: 8px;
        selection-background-color: #334155;
        selection-color: white;
        padding: 4px;
    }
    QRadioButton {
        color: #E2E8F0;
    }
    QRadioButton::indicator {
        border-color: #475569;
        background: #1E293B;
    }
    QRadioButton::indicator:checked {
        border-color: #60A5FA;
        background: qradialgradient(cx:0.5, cy:0.5, radius:0.4, fx:0.5, fy:0.5, stop:0 #60A5FA, stop:1 #60A5FA);
    }
    QCheckBox {
        color: #E2E8F0;
    }
    QCheckBox::indicator {
        border-color: #475569;
        background: #1E293B;
    }
    QCheckBox::indicator:checked {
        background: #3B82F6;
        border-color: #3B82F6;
    }
    QLabel#ItemTitle {
        color: #F1F5F9;
    }
    QLabel#ItemDetail {
        color: #94A3B8;
    }
    QLabel#AppBarTitle {
        color: #F8FAFC;
    }
    QLabel#AppBarVersion {
        color: #64748B;
    }
    QLabel#SectionTitle {
        color: #94A3B8;
    }
    QLabel#StatsLabel {
        color: #64748B;
    }
    QToolButton#LayoutCard {
        background-color: #1E293B;
        border: 2px solid #475569;
        border-radius: 14px;
    }
    QToolButton#LayoutCard:hover {
        border-color: #60A5FA;
        background-color: #334155;
    }
    QToolButton#LayoutCard:checked {
        border-color: #3B82F6;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #1E3A8A, stop:1 #1E293B);
    }
    QToolTip {
        background-color: #334155;
        color: white;
        border: 1px solid #475569;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }
    """ + SCROLLBAR_CSS

    @staticmethod
    def apply(app, mode="Light"):
        if mode == "Auto":
            mode = "Light"
        if mode == "Dark":
            app.setStyleSheet(ThemeManager.CSS_DARK)
            return "#E2E8F0"
        else:
            app.setStyleSheet(ThemeManager.CSS_LIGHT)
            return "#475569"
