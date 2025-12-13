"""
数据库模块
提供发票历史记录的持久化存储和查询功能
"""
import os
import sqlite3
import platform
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import contextmanager


class InvoiceDatabase:
    """发票数据库管理器"""
    
    def __init__(self, db_path: str = None):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径，默认为用户数据目录
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path or self._get_default_db_path()
        self._ensure_db_dir()
        self._init_db()
    
    @staticmethod
    def _get_default_db_path() -> str:
        """获取跨平台默认数据库路径"""
        system = platform.system()
        if system == "Windows":
            base = os.environ.get('APPDATA', os.path.expanduser('~'))
            return os.path.join(base, 'InvoiceMaster', 'invoices.db')
        elif system == "Darwin":  # macOS
            return os.path.expanduser('~/Library/Application Support/InvoiceMaster/invoices.db')
        else:  # Linux/UOS
            return os.path.expanduser('~/.local/share/InvoiceMaster/invoices.db')
    
    def _ensure_db_dir(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            self.logger.info(f"创建数据库目录: {db_dir}")
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_db(self):
        """初始化数据库表结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 发票主表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    invoice_code TEXT,
                    invoice_number TEXT,
                    invoice_date TEXT,
                    amount REAL DEFAULT 0,
                    amount_without_tax REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    tax_rate TEXT,
                    seller_name TEXT,
                    seller_tax_id TEXT,
                    buyer_name TEXT,
                    buyer_tax_id TEXT,
                    invoice_type TEXT,
                    item_name TEXT,
                    check_code TEXT,
                    machine_code TEXT,
                    remark TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted INTEGER DEFAULT 0,
                    UNIQUE(file_path)
                )
            """)
            
            # 导出记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS export_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    export_path TEXT NOT NULL,
                    export_type TEXT DEFAULT 'excel',
                    invoice_count INTEGER DEFAULT 0,
                    total_amount REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 打印记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS print_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    printer_name TEXT,
                    layout_mode TEXT,
                    paper_size TEXT,
                    copies INTEGER DEFAULT 1,
                    invoice_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_seller ON invoices(seller_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_amount ON invoices(amount)")
            
            self.logger.info(f"数据库初始化完成: {self.db_path}")
    
    # ==================== 发票 CRUD ====================
    
    def save_invoice(self, invoice_data: Dict[str, Any]) -> int:
        """
        保存或更新发票记录
        
        Args:
            invoice_data: 发票数据字典
            
        Returns:
            发票记录 ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查是否已存在
            cursor.execute("SELECT id FROM invoices WHERE file_path = ?", (invoice_data.get('file_path', ''),))
            existing = cursor.fetchone()
            
            if existing:
                # 更新
                cursor.execute("""
                    UPDATE invoices SET
                        file_name = ?,
                        invoice_code = ?,
                        invoice_number = ?,
                        invoice_date = ?,
                        amount = ?,
                        amount_without_tax = ?,
                        tax_amount = ?,
                        tax_rate = ?,
                        seller_name = ?,
                        seller_tax_id = ?,
                        buyer_name = ?,
                        buyer_tax_id = ?,
                        invoice_type = ?,
                        item_name = ?,
                        check_code = ?,
                        machine_code = ?,
                        remark = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    invoice_data.get('file_name', ''),
                    invoice_data.get('code', ''),
                    invoice_data.get('number', ''),
                    invoice_data.get('date', ''),
                    float(invoice_data.get('amount', 0) or 0),
                    float(invoice_data.get('amount_without_tax', 0) or 0),
                    float(invoice_data.get('tax_amt', 0) or 0),
                    invoice_data.get('tax_rate', ''),
                    invoice_data.get('seller', ''),
                    invoice_data.get('seller_tax_id', ''),
                    invoice_data.get('buyer', ''),
                    invoice_data.get('buyer_tax_id', ''),
                    invoice_data.get('invoice_type', ''),
                    invoice_data.get('item_name', ''),
                    invoice_data.get('check_code', ''),
                    invoice_data.get('machine_code', ''),
                    invoice_data.get('remark', ''),
                    existing['id']
                ))
                return existing['id']
            else:
                # 插入
                cursor.execute("""
                    INSERT INTO invoices (
                        file_path, file_name, invoice_code, invoice_number, 
                        invoice_date, amount, amount_without_tax, tax_amount,
                        tax_rate, seller_name, seller_tax_id, buyer_name,
                        buyer_tax_id, invoice_type, item_name, check_code,
                        machine_code, remark
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    invoice_data.get('file_path', ''),
                    invoice_data.get('file_name', ''),
                    invoice_data.get('code', ''),
                    invoice_data.get('number', ''),
                    invoice_data.get('date', ''),
                    float(invoice_data.get('amount', 0) or 0),
                    float(invoice_data.get('amount_without_tax', 0) or 0),
                    float(invoice_data.get('tax_amt', 0) or 0),
                    invoice_data.get('tax_rate', ''),
                    invoice_data.get('seller', ''),
                    invoice_data.get('seller_tax_id', ''),
                    invoice_data.get('buyer', ''),
                    invoice_data.get('buyer_tax_id', ''),
                    invoice_data.get('invoice_type', ''),
                    invoice_data.get('item_name', ''),
                    invoice_data.get('check_code', ''),
                    invoice_data.get('machine_code', ''),
                    invoice_data.get('remark', '')
                ))
                return cursor.lastrowid
    
    def get_invoice(self, invoice_id: int) -> Optional[Dict]:
        """获取单个发票"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices WHERE id = ? AND is_deleted = 0", (invoice_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_invoices(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """获取发票列表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM invoices 
                WHERE is_deleted = 0 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return [dict(row) for row in cursor.fetchall()]
    
    def search_invoices(
        self,
        keyword: str = None,
        date_from: str = None,
        date_to: str = None,
        amount_min: float = None,
        amount_max: float = None,
        seller: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        搜索发票
        
        Args:
            keyword: 关键词（匹配发票号、销售方、商品名）
            date_from: 开始日期 (YYYY-MM-DD)
            date_to: 结束日期 (YYYY-MM-DD)
            amount_min: 最小金额
            amount_max: 最大金额
            seller: 销售方名称
            limit: 返回数量限制
        """
        conditions = ["is_deleted = 0"]
        params = []
        
        if keyword:
            conditions.append(
                "(invoice_number LIKE ? OR seller_name LIKE ? OR item_name LIKE ? OR buyer_name LIKE ?)"
            )
            keyword_pattern = f"%{keyword}%"
            params.extend([keyword_pattern] * 4)
        
        if date_from:
            conditions.append("invoice_date >= ?")
            params.append(date_from)
        
        if date_to:
            conditions.append("invoice_date <= ?")
            params.append(date_to)
        
        if amount_min is not None:
            conditions.append("amount >= ?")
            params.append(amount_min)
        
        if amount_max is not None:
            conditions.append("amount <= ?")
            params.append(amount_max)
        
        if seller:
            conditions.append("seller_name LIKE ?")
            params.append(f"%{seller}%")
        
        query = f"""
            SELECT * FROM invoices 
            WHERE {' AND '.join(conditions)}
            ORDER BY invoice_date DESC
            LIMIT ?
        """
        params.append(limit)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_invoice(self, invoice_id: int, soft: bool = True) -> bool:
        """删除发票（默认软删除）"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if soft:
                cursor.execute("UPDATE invoices SET is_deleted = 1 WHERE id = ?", (invoice_id,))
            else:
                cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
            return cursor.rowcount > 0
    
    def get_statistics(self, date_from: str = None, date_to: str = None) -> Dict:
        """获取统计信息"""
        conditions = ["is_deleted = 0"]
        params = []
        
        if date_from:
            conditions.append("invoice_date >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("invoice_date <= ?")
            params.append(date_to)
        
        where_clause = ' AND '.join(conditions)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_count,
                    SUM(amount) as total_amount,
                    SUM(tax_amount) as total_tax,
                    AVG(amount) as avg_amount,
                    MIN(amount) as min_amount,
                    MAX(amount) as max_amount
                FROM invoices WHERE {where_clause}
            """, params)
            row = cursor.fetchone()
            return dict(row) if row else {}
    
    # ==================== 导出/打印记录 ====================
    
    def save_export_record(self, export_path: str, invoice_count: int, total_amount: float):
        """保存导出记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO export_history (export_path, invoice_count, total_amount)
                VALUES (?, ?, ?)
            """, (export_path, invoice_count, total_amount))
    
    def save_print_record(self, printer_name: str, layout_mode: str, paper_size: str, copies: int, invoice_count: int):
        """保存打印记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO print_history (printer_name, layout_mode, paper_size, copies, invoice_count)
                VALUES (?, ?, ?, ?, ?)
            """, (printer_name, layout_mode, paper_size, copies, invoice_count))
    
    def get_recent_exports(self, limit: int = 10) -> List[Dict]:
        """获取最近导出记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM export_history ORDER BY created_at DESC LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
