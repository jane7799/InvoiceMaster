"""
OCR 引擎单元测试
"""
import os
import sys
import unittest
import tempfile

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.ocr_engine import InvoiceHelper


class TestInvoiceHelper(unittest.TestCase):
    """InvoiceHelper 测试用例"""
    
    def test_parse_amount_local_empty(self):
        """测试空文件解析"""
        amount, date = InvoiceHelper.parse_amount_local("/nonexistent/file.pdf")
        self.assertEqual(amount, 0.0)
        self.assertEqual(date, "")
    
    def test_thumb_nonexistent(self):
        """测试不存在文件的缩略图"""
        result = InvoiceHelper.thumb("/nonexistent/file.pdf")
        # 应该返回 None 或默认图标
        self.assertIsNone(result)


class TestInvoiceHelperIntegration(unittest.TestCase):
    """OCR 集成测试（需要网络和 API 配置）"""
    
    @unittest.skip("需要 API 配置")
    def test_ocr_with_baidu(self):
        """测试百度 OCR（需要有效 API Key）"""
        # 这个测试需要真实的 API Key 和测试文件
        pass


if __name__ == '__main__':
    unittest.main()
