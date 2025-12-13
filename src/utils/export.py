"""
导出模块
提供多种格式的数据导出功能
"""
import os
import csv
import json
import logging
from datetime import datetime
from typing import List, Dict, Any


class ExportManager:
    """导出管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def export_to_csv(self, data: List[Dict], output_path: str, encoding: str = 'utf-8-sig') -> bool:
        """
        导出数据到 CSV 文件
        
        Args:
            data: 发票数据列表
            output_path: 输出文件路径
            encoding: 文件编码 (默认 utf-8-sig 支持 Excel 中文)
            
        Returns:
            是否成功
        """
        try:
            if not data:
                self.logger.warning("导出数据为空")
                return False
            
            # 定义 CSV 列
            fieldnames = [
                '序号', '文件名', '开票日期', '发票代码', '发票号码',
                '价税合计', '不含税金额', '税额', '税率',
                '销售方', '销售方税号', '购买方', '购买方税号',
                '发票类型', '商品名称', '备注', '导入时间'
            ]
            
            with open(output_path, 'w', newline='', encoding=encoding) as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for idx, item in enumerate(data, 1):
                    ext = item.get('ext', {})
                    row = {
                        '序号': idx,
                        '文件名': item.get('n', ''),
                        '开票日期': item.get('d', '') or ext.get('date', ''),
                        '发票代码': ext.get('code', ''),
                        '发票号码': ext.get('number', ''),
                        '价税合计': item.get('a', 0),
                        '不含税金额': ext.get('amount_without_tax', ''),
                        '税额': ext.get('tax_amt', ''),
                        '税率': ext.get('tax_rate', ''),
                        '销售方': ext.get('seller', ''),
                        '销售方税号': ext.get('seller_tax_id', ''),
                        '购买方': ext.get('buyer', ''),
                        '购买方税号': ext.get('buyer_tax_id', ''),
                        '发票类型': ext.get('invoice_type', ''),
                        '商品名称': ext.get('item_name', ''),
                        '备注': ext.get('remark', ''),
                        '导入时间': datetime.now().strftime('%Y-%m-%d %H:%M')
                    }
                    writer.writerow(row)
            
            self.logger.info(f"CSV 导出成功: {output_path}, 共 {len(data)} 条")
            return True
        except Exception as e:
            self.logger.error(f"CSV 导出失败: {str(e)}")
            return False
    
    def export_to_json(self, data: List[Dict], output_path: str) -> bool:
        """
        导出数据到 JSON 文件
        
        Args:
            data: 发票数据列表
            output_path: 输出文件路径
            
        Returns:
            是否成功
        """
        try:
            if not data:
                self.logger.warning("导出数据为空")
                return False
            
            export_data = []
            for idx, item in enumerate(data, 1):
                ext = item.get('ext', {})
                export_data.append({
                    'index': idx,
                    'file_name': item.get('n', ''),
                    'file_path': item.get('p', ''),
                    'date': item.get('d', '') or ext.get('date', ''),
                    'amount': item.get('a', 0),
                    'amount_without_tax': ext.get('amount_without_tax', ''),
                    'tax_amount': ext.get('tax_amt', ''),
                    'tax_rate': ext.get('tax_rate', ''),
                    'seller': ext.get('seller', ''),
                    'seller_tax_id': ext.get('seller_tax_id', ''),
                    'buyer': ext.get('buyer', ''),
                    'buyer_tax_id': ext.get('buyer_tax_id', ''),
                    'invoice_code': ext.get('code', ''),
                    'invoice_number': ext.get('number', ''),
                    'invoice_type': ext.get('invoice_type', ''),
                    'item_name': ext.get('item_name', ''),
                    'remark': ext.get('remark', ''),
                    'exported_at': datetime.now().isoformat()
                })
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'version': '1.0',
                    'export_time': datetime.now().isoformat(),
                    'total_count': len(export_data),
                    'total_amount': sum(item.get('a', 0) for item in data),
                    'invoices': export_data
                }, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"JSON 导出成功: {output_path}, 共 {len(data)} 条")
            return True
        except Exception as e:
            self.logger.error(f"JSON 导出失败: {str(e)}")
            return False
    
    def get_summary_text(self, data: List[Dict]) -> str:
        """
        生成导出摘要文本
        
        Args:
            data: 发票数据列表
            
        Returns:
            摘要文本
        """
        if not data:
            return "无数据"
        
        total_amount = sum(item.get('a', 0) for item in data)
        return f"共 {len(data)} 张发票，合计金额：¥{total_amount:,.2f}"


# 全局导出管理器实例
export_manager = ExportManager()
