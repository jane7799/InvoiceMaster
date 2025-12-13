"""
PDF 引擎单元测试
"""
import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.pdf_engine import PDFEngine


class TestPDFEngine(unittest.TestCase):
    """PDFEngine 测试用例"""
    
    def test_sizes_defined(self):
        """测试纸张尺寸定义"""
        self.assertIn("A4", PDFEngine.SIZES)
        self.assertIn("A5", PDFEngine.SIZES)
        self.assertIn("B5", PDFEngine.SIZES)
        
        # A4 尺寸约 595x842 点
        a4 = PDFEngine.SIZES["A4"]
        self.assertEqual(a4[0], 595)
        self.assertEqual(a4[1], 842)
    
    def test_merge_empty_files(self):
        """测试空文件列表合并"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            out_path = f.name
        
        try:
            PDFEngine.merge([], mode="1x1", paper="A4", out_path=out_path)
            self.assertTrue(os.path.exists(out_path))
            self.assertGreater(os.path.getsize(out_path), 0)
        finally:
            if os.path.exists(out_path):
                os.remove(out_path)
    
    def test_merge_modes(self):
        """测试不同布局模式"""
        for mode in ["1x1", "1x2", "2x2"]:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                out_path = f.name
            
            try:
                PDFEngine.merge([], mode=mode, paper="A4", out_path=out_path)
                self.assertTrue(os.path.exists(out_path), f"模式 {mode} 失败")
            finally:
                if os.path.exists(out_path):
                    os.remove(out_path)


if __name__ == '__main__':
    unittest.main()
