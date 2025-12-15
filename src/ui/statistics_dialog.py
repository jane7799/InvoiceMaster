
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, 
                           QPushButton, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
from src.core.database import get_db

class StatisticsDialog(QDialog):
    """统计报表对话框（显示当前导入的发票）"""
    
    def __init__(self, parent=None, current_data=None):
        super().__init__(parent)
        self.setWindowTitle("统计报表")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        self.current_data = current_data or []  # 当前会话数据
        
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
        
        self.total_count_card, self.total_count_value = self._create_stat_card("总发票数", "0 张", "#3B82F6")
        self.total_amount_card, self.total_amount_value = self._create_stat_card("总金额", "¥0.00", "#10B981")
        self.total_tax_card, self.total_tax_value = self._create_stat_card("总税额", "¥0.00", "#F59E0B")
        
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
        """创建统计卡片，返回 (card, value_label) 元组"""
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
        
        # 返回卡片和值标签，便于后续更新
        return card, lbl_value
        
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
        """加载统计数据（基于当前导入的发票）"""
        # 从当前数据计算统计
        ignored_types = ["发票清单", "非发票凭证"]
        
        total_count = 0
        total_amount = 0.0
        total_tax = 0.0
        by_type = {}  # type -> {count, amount}
        by_month = {}  # month -> {count, amount}
        
        for d in self.current_data:
            ext = d.get("ext", {})
            inv_type = ext.get("invoice_type", "") or "未分类"
            
            # 排除清单和非发票凭证
            if inv_type in ignored_types or "非发票" in inv_type:
                continue
            
            amount = d.get("a", 0) or 0
            tax_amt = float(ext.get("tax_amt", 0) or 0)
            date = d.get("d", "") or ""
            month = date[:7] if len(date) >= 7 else "未知"
            
            total_count += 1
            total_amount += amount
            total_tax += tax_amt
            
            # 按类型统计
            if inv_type not in by_type:
                by_type[inv_type] = {"count": 0, "amount": 0.0}
            by_type[inv_type]["count"] += 1
            by_type[inv_type]["amount"] += amount
            
            # 按月份统计
            if month not in by_month:
                by_month[month] = {"count": 0, "amount": 0.0}
            by_month[month]["count"] += 1
            by_month[month]["amount"] += amount
        
        # 更新卡片
        self.total_count_value.setText(f"{total_count} 张")
        self.total_amount_value.setText(f"¥{total_amount:,.2f}")
        self.total_tax_value.setText(f"¥{total_tax:,.2f}")
        
        # 更新类型表（按金额排序）
        type_list = sorted(by_type.items(), key=lambda x: x[1]["amount"], reverse=True)
        self.type_table.setRowCount(len(type_list))
        for i, (t, data) in enumerate(type_list):
            self.type_table.setItem(i, 0, QTableWidgetItem(t))
            self.type_table.setItem(i, 1, QTableWidgetItem(f"{data['count']} 张"))
            self.type_table.setItem(i, 2, QTableWidgetItem(f"¥{data['amount']:,.2f}"))
            
        # 更新月份表（按月份排序）
        month_list = sorted(by_month.items(), key=lambda x: x[0], reverse=True)
        self.month_table.setRowCount(len(month_list))
        for i, (m, data) in enumerate(month_list):
            self.month_table.setItem(i, 0, QTableWidgetItem(m))
            self.month_table.setItem(i, 1, QTableWidgetItem(f"{data['count']} 张"))
            self.month_table.setItem(i, 2, QTableWidgetItem(f"¥{data['amount']:,.2f}"))
