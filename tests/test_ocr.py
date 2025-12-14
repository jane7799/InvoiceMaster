"""
OCR 引擎单元测试
"""
import os
import sys
import unittest

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.invoice_helper import InvoiceHelper
from PyQt6.QtGui import QGuiApplication

class TestInvoiceHelper(unittest.TestCase):
    """InvoiceHelper 测试用例"""
    
    @classmethod
    def setUpClass(cls):
        # 创建 QGuiApplication 实例以支持 QPixmap
        cls.app = QGuiApplication(sys.argv)

    def test_parse_amount_local_empty(self):
        """测试空文件解析"""
        # parse_invoice_local returns a dict
        result = InvoiceHelper.parse_invoice_local("/nonexistent/file.pdf")
        self.assertEqual(result.get('amount', 0), 0.0)
        self.assertEqual(result.get('date', ''), "")
    
    def test_thumb_nonexistent(self):
        """测试不存在文件的缩略图"""
        # 应该返回默认图标的 QPixmap
        result = InvoiceHelper.thumb("/nonexistent/file.pdf")
        self.assertIsNotNone(result)
        # 验证是 QPixmap
        from PyQt6.QtGui import QPixmap
        self.assertIsInstance(result, QPixmap)


class TestInvoiceHelperIntegration(unittest.TestCase):
    """OCR 集成测试（需要网络和 API 配置）"""
    
    @unittest.skip("需要 API 配置")
    def test_ocr_with_baidu(self):
        """测试百度 OCR（需要有效 API Key）"""
        pass


if __name__ == '__main__':
    unittest.main()
