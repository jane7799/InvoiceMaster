"""
数据库单元测试
"""
import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import InvoiceDatabase

class TestInvoiceDatabase(unittest.TestCase):
    """InvoiceDatabase 测试用例"""
    
    def setUp(self):
        """测试前创建临时数据库"""
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_file.close()
        self.db = InvoiceDatabase(self.temp_file.name)
    
    def tearDown(self):
        """测试后清理临时文件"""
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)
    
    def test_save_and_get_invoice(self):
        """测试保存和获取发票"""
        invoice_data = {
            'file_path': '/test/invoice1.pdf',
            'file_name': 'invoice1.pdf',
            'code': '123456',
            'number': 'INV001',
            'date': '2025-12-13',
            'amount': 1000.50,
            'seller': '测试公司A',
            'buyer': '测试公司B'
        }
        
        invoice_id = self.db.save_invoice(invoice_data)
        self.assertIsInstance(invoice_id, int)
        self.assertGreater(invoice_id, 0)
        
        # 获取
        invoice = self.db.get_invoice_by_path('/test/invoice1.pdf')
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice['file_name'], 'invoice1.pdf')
        self.assertAlmostEqual(invoice['amount'], 1000.50)
    
    def test_update_invoice(self):
        """测试更新发票"""
        invoice_data = {
            'file_path': '/test/invoice2.pdf',
            'file_name': 'invoice2.pdf',
            'amount': 500.00
        }
        
        invoice_id = self.db.save_invoice(invoice_data)
        
        # 更新
        invoice_data['amount'] = 800.00
        updated_id = self.db.save_invoice(invoice_data)
        
        self.assertEqual(invoice_id, updated_id)
        
        invoice = self.db.get_invoice_by_path('/test/invoice2.pdf')
        self.assertAlmostEqual(invoice['amount'], 800.00)
    
    def test_search_invoices(self):
        """测试搜索发票"""
        # 插入测试数据
        self.db.save_invoice({
            'file_path': '/test/a.pdf',
            'file_name': 'a.pdf',
            'seller': '北京科技公司',
            'date': '2025-01-01',
            'amount': 1000
        })
        self.db.save_invoice({
            'file_path': '/test/b.pdf',
            'file_name': 'b.pdf',
            'seller': '上海贸易公司',
            'date': '2025-02-01',
            'amount': 2000
        })
        
        # 按卖方搜索
        results = self.db.search_invoices(seller='北京')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['seller'], '北京科技公司')
        
        # 按金额范围搜索
        results = self.db.search_invoices(min_amount=1500)
        self.assertEqual(len(results), 1)
        self.assertAlmostEqual(results[0]['amount'], 2000)
    
    def test_delete_invoice(self):
        """测试删除发票"""
        self.db.save_invoice({
            'file_path': '/test/delete.pdf',
            'file_name': 'delete.pdf'
        })
        
        # 删除
        result = self.db.delete_invoice('/test/delete.pdf')
        self.assertTrue(result)
        
        # 删除后无法查询
        invoice = self.db.get_invoice_by_path('/test/delete.pdf')
        self.assertIsNone(invoice)
    
    def test_statistics(self):
        """测试统计功能"""
        self.db.save_invoice({'file_path': '/test/s1.pdf', 'file_name': 's1.pdf', 'amount': 100, 'invoice_type': 'A', 'date': '2025-01-01'})
        self.db.save_invoice({'file_path': '/test/s2.pdf', 'file_name': 's2.pdf', 'amount': 200, 'invoice_type': 'A', 'date': '2025-01-05'})
        self.db.save_invoice({'file_path': '/test/s3.pdf', 'file_name': 's3.pdf', 'amount': 300, 'invoice_type': 'B', 'date': '2025-02-01'})
        
        stats = self.db.get_statistics()
        
        self.assertEqual(stats['total_count'], 3)
        self.assertAlmostEqual(stats['total_amount'], 600)
        
        # 验证按月统计
        by_month = stats['by_month']
        # 应该有 2025-01 和 2025-02
        months = [m['month'] for m in by_month]
        self.assertIn('2025-01', months)
        self.assertIn('2025-02', months)

if __name__ == '__main__':
    unittest.main()
