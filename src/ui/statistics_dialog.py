
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, 
                           QPushButton, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
from src.core.database import get_db

class StatisticsDialog(QDialog):
    """统计报表对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("统计报表")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        self._setup_ui()
        self._load_statistics()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("📊 发票统计报表")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1E293B;")
        layout.addWidget(title)
        
        # 汇总卡片区
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        self.total_count_card = self._create_stat_card("总发票数", "0 张", "#3B82F6")
        self.total_amount_card = self._create_stat_card("总金额", "¥0.00", "#10B981")
        self.total_tax_card = self._create_stat_card("总税额", "¥0.00", "#F59E0B")
        
        cards_layout.addWidget(self.total_count_card)
        cards_layout.addWidget(self.total_amount_card)
        cards_layout.addWidget(self.total_tax_card)
        layout.addLayout(cards_layout)
        
        # 分组统计区
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E2E8F0; border-radius: 8px; background: white; }
            QTabBar::tab { padding: 10px 20px; font-weight: 500; }
            QTabBar::tab:selected { background: #3B82F6; color: white; border-radius: 8px 8px 0 0; }
        """)
        
        # 按类型统计
        self.type_table = self._create_table(["发票类型", "数量", "金额"])
        tabs.addTab(self.type_table, "按类型")
        
        # 按月份统计
        self.month_table = self._create_table(["月份", "数量", "金额"])
        tabs.addTab(self.month_table, "按月份")
        
        layout.addWidget(tabs, 1)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._load_statistics)
        refresh_btn.setStyleSheet("""
            QPushButton { 
                background: #F1F5F9; border: 1px solid #E2E8F0; 
                border-radius: 8px; padding: 10px 24px; 
                color: #475569; font-weight: 500;
            }
            QPushButton:hover { background: #E2E8F0; }
        """)
        btn_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton { 
                background: #3B82F6; border: none; 
                border-radius: 8px; padding: 10px 24px; 
                color: white; font-weight: 500;
            }
            QPushButton:hover { background: #2563EB; }
        """)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
    def _create_stat_card(self, title, value, color):
        """创建统计卡片"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 12px;
                border-left: 4px solid {color};
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 2)
        card.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(card)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #64748B; font-size: 13px;")
        layout.addWidget(lbl_title)
        
        lbl_value = QLabel(value)
        lbl_value.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
        layout.addWidget(lbl_value)
        
        return card
        
    def _create_table(self, headers):
        """创建统计表格"""
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #F8FAFC;
                padding: 8px;
                border: none;
                font-weight: 600;
                color: #475569;
            }
        """)
        
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        table.setStyleSheet("""
            QTableWidget { border: none; }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:selected { background-color: #EFF6FF; color: #1E293B; }
        """)
        
        return table
        
    def _load_statistics(self):
        """加载统计数据"""
        stats = get_db().get_statistics()
        
        # 更新卡片
        self.total_count_card.findChild(QLabel, "").nextInFocusChain().setText(f"{stats.get('total_count', 0)} 张")
        self.total_amount_card.findChild(QLabel, "").nextInFocusChain().setText(f"¥{stats.get('total_amount', 0):,.2f}")
        self.total_tax_card.findChild(QLabel, "").nextInFocusChain().setText(f"¥{stats.get('total_tax', 0):,.2f}")
        
        # 更新类型表
        by_type = stats.get("by_type", [])
        self.type_table.setRowCount(len(by_type))
        for i, item in enumerate(by_type):
            self.type_table.setItem(i, 0, QTableWidgetItem(str(item["type"])))
            self.type_table.setItem(i, 1, QTableWidgetItem(f"{item['count']} 张"))
            self.type_table.setItem(i, 2, QTableWidgetItem(f"¥{item['amount']:,.2f}"))
            
        # 更新月份表
        by_month = stats.get("by_month", [])
        self.month_table.setRowCount(len(by_month))
        for i, item in enumerate(by_month):
            self.month_table.setItem(i, 0, QTableWidgetItem(str(item["month"])))
            self.month_table.setItem(i, 1, QTableWidgetItem(f"{item['count']} 张"))
            self.month_table.setItem(i, 2, QTableWidgetItem(f"¥{item['amount']:,.2f}"))
