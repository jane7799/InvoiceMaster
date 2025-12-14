"""
发票数据库模块
使用 SQLite 存储发票历史记录，支持查询和统计
"""
import os
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional


class InvoiceDatabase:
    """发票数据库管理类"""
    
    def __init__(self, db_path: str = None):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径，默认为用户目录下的 .invoicemaster/invoices.db
        """
        if db_path is None:
            # 默认存储位置
            app_dir = os.path.expanduser("~/.invoicemaster")
            os.makedirs(app_dir, exist_ok=True)
            db_path = os.path.join(app_dir, "invoices.db")
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建发票表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE,
                file_name TEXT,
                invoice_type TEXT,
                date TEXT,
                amount REAL DEFAULT 0,
                amount_without_tax REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,
                buyer TEXT,
                buyer_tax_id TEXT,
                seller TEXT,
                seller_tax_id TEXT,
                invoice_number TEXT,
                invoice_code TEXT,
                check_code TEXT,
                item_name TEXT,
                remark TEXT,
                raw_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON invoices(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoice_type ON invoices(invoice_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_buyer ON invoices(buyer)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_seller ON invoices(seller)')
        
        conn.commit()
        conn.close()
    
    def save_invoice(self, data: Dict) -> int:
        """
        保存或更新发票记录
        
        Args:
            data: 发票数据字典
            
        Returns:
            发票记录 ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        file_path = data.get("file_path", "")
        
        # 检查是否已存在
        cursor.execute('SELECT id FROM invoices WHERE file_path = ?', (file_path,))
        existing = cursor.fetchone()
        
        if existing:
            # 更新现有记录
            cursor.execute('''
                UPDATE invoices SET
                    file_name = ?,
                    invoice_type = ?,
                    date = ?,
                    amount = ?,
                    amount_without_tax = ?,
                    tax_amount = ?,
                    buyer = ?,
                    buyer_tax_id = ?,
                    seller = ?,
                    seller_tax_id = ?,
                    invoice_number = ?,
                    invoice_code = ?,
                    check_code = ?,
                    item_name = ?,
                    remark = ?,
                    raw_data = ?,
                    updated_at = ?
                WHERE file_path = ?
            ''', (
                data.get("file_name", os.path.basename(file_path)),
                data.get("invoice_type", ""),
                data.get("date", ""),
                float(data.get("amount", 0) or 0),
                float(data.get("amount_without_tax", 0) or 0),
                float(data.get("tax_amt", 0) or 0),
                data.get("buyer", ""),
                data.get("buyer_tax_id", ""),
                data.get("seller", ""),
                data.get("seller_tax_id", ""),
                data.get("number", ""),
                data.get("code", ""),
                data.get("check_code", ""),
                data.get("item_name", ""),
                data.get("remark", ""),
                json.dumps(data, ensure_ascii=False),
                datetime.now().isoformat(),
                file_path
            ))
            invoice_id = existing[0]
        else:
            # 插入新记录
            cursor.execute('''
                INSERT INTO invoices (
                    file_path, file_name, invoice_type, date, amount,
                    amount_without_tax, tax_amount, buyer, buyer_tax_id,
                    seller, seller_tax_id, invoice_number, invoice_code,
                    check_code, item_name, remark, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_path,
                data.get("file_name", os.path.basename(file_path)),
                data.get("invoice_type", ""),
                data.get("date", ""),
                float(data.get("amount", 0) or 0),
                float(data.get("amount_without_tax", 0) or 0),
                float(data.get("tax_amt", 0) or 0),
                data.get("buyer", ""),
                data.get("buyer_tax_id", ""),
                data.get("seller", ""),
                data.get("seller_tax_id", ""),
                data.get("number", ""),
                data.get("code", ""),
                data.get("check_code", ""),
                data.get("item_name", ""),
                data.get("remark", ""),
                json.dumps(data, ensure_ascii=False)
            ))
            invoice_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return invoice_id
    
    def get_invoice_by_path(self, file_path: str) -> Optional[Dict]:
        """根据文件路径获取发票记录"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM invoices WHERE file_path = ?', (file_path,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_all_invoices(self, limit: int = 1000) -> List[Dict]:
        """获取所有发票记录"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM invoices ORDER BY date DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def search_invoices(self, 
                       start_date: str = None,
                       end_date: str = None,
                       invoice_type: str = None,
                       buyer: str = None,
                       seller: str = None,
                       min_amount: float = None,
                       max_amount: float = None) -> List[Dict]:
        """搜索发票"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        conditions = []
        params = []
        
        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        if invoice_type:
            conditions.append("invoice_type LIKE ?")
            params.append(f"%{invoice_type}%")
        if buyer:
            conditions.append("buyer LIKE ?")
            params.append(f"%{buyer}%")
        if seller:
            conditions.append("seller LIKE ?")
            params.append(f"%{seller}%")
        if min_amount is not None:
            conditions.append("amount >= ?")
            params.append(min_amount)
        if max_amount is not None:
            conditions.append("amount <= ?")
            params.append(max_amount)
        
        query = "SELECT * FROM invoices"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY date DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def delete_invoice(self, file_path: str) -> bool:
        """删除发票记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM invoices WHERE file_path = ?', (file_path,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return deleted
    
    def get_statistics(self, year: int = None, month: int = None) -> Dict:
        """
        获取统计数据
        
        Args:
            year: 年份（可选）
            month: 月份（可选）
            
        Returns:
            统计数据字典
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        conditions = []
        params = []
        
        if year:
            conditions.append("strftime('%Y', date) = ?")
            params.append(str(year))
        if month:
            conditions.append("strftime('%m', date) = ?")
            params.append(f"{month:02d}")
        
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        # [V3.5] 统计时排除清单和非发票凭证
        exclude_condition = "invoice_type != '发票清单' AND invoice_type != '非发票凭证' AND invoice_type NOT LIKE '非发票%'"
        
        if where_clause:
            where_clause += f" AND {exclude_condition}"
        else:
            where_clause = f"WHERE {exclude_condition}"
        
        # 总金额统计
        cursor.execute(f'''
            SELECT 
                COUNT(*) as total_count,
                COALESCE(SUM(amount), 0) as total_amount,
                COALESCE(SUM(tax_amount), 0) as total_tax
            FROM invoices {where_clause}
        ''', params)
        totals = cursor.fetchone()
        
        # 按类型分组统计
        cursor.execute(f'''
            SELECT 
                invoice_type,
                COUNT(*) as count,
                COALESCE(SUM(amount), 0) as amount
            FROM invoices {where_clause}
            GROUP BY invoice_type
            ORDER BY amount DESC
        ''', params)
        by_type = cursor.fetchall()
        
        # 按月份分组统计
        cursor.execute(f'''
            SELECT 
                strftime('%Y-%m', date) as month,
                COUNT(*) as count,
                COALESCE(SUM(amount), 0) as amount
            FROM invoices {where_clause}
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month DESC
            LIMIT 12
        ''', params)
        by_month = cursor.fetchall()
        
        conn.close()
        
        return {
            "total_count": totals[0],
            "total_amount": totals[1],
            "total_tax": totals[2],
            "by_type": [{"type": row[0] or "未分类", "count": row[1], "amount": row[2]} for row in by_type],
            "by_month": [{"month": row[0] or "未知", "count": row[1], "amount": row[2]} for row in by_month]
        }
    
    def clear_all(self) -> int:
        """清空所有记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM invoices')
        deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        return deleted


# 全局数据库实例
_db_instance = None

def get_db() -> InvoiceDatabase:
    """获取数据库单例实例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = InvoiceDatabase()
    return _db_instance
