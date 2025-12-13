"""
快捷键管理模块
提供应用级键盘快捷键绑定
"""
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtCore import Qt


class ShortcutManager:
    """
    快捷键管理器
    
    用法:
        shortcut_manager = ShortcutManager(main_window)
        shortcut_manager.register('Ctrl+O', main_window.open_file)
        shortcut_manager.register('Ctrl+P', main_window.print_action)
    """
    
    # 预定义快捷键配置
    DEFAULT_SHORTCUTS = {
        'open_file': 'Ctrl+O',
        'save_excel': 'Ctrl+E',
        'print': 'Ctrl+P',
        'delete': 'Delete',
        'select_all': 'Ctrl+A',
        'clear': 'Ctrl+Shift+C',
        'settings': 'Ctrl+,',
        'zoom_in': 'Ctrl++',
        'zoom_out': 'Ctrl+-',
        'help': 'F1',
        'quit': 'Ctrl+Q',
    }
    
    def __init__(self, parent: QMainWindow):
        self.parent = parent
        self.shortcuts = {}
    
    def register(self, key_sequence: str, callback, context=Qt.ShortcutContext.WindowShortcut):
        """
        注册快捷键
        
        Args:
            key_sequence: 快捷键字符串，如 'Ctrl+O'
            callback: 回调函数
            context: 快捷键上下文
        """
        shortcut = QShortcut(QKeySequence(key_sequence), self.parent)
        shortcut.setContext(context)
        shortcut.activated.connect(callback)
        self.shortcuts[key_sequence] = shortcut
        return shortcut
    
    def unregister(self, key_sequence: str):
        """注销快捷键"""
        if key_sequence in self.shortcuts:
            self.shortcuts[key_sequence].setEnabled(False)
            del self.shortcuts[key_sequence]
    
    def enable(self, key_sequence: str, enabled: bool = True):
        """启用/禁用快捷键"""
        if key_sequence in self.shortcuts:
            self.shortcuts[key_sequence].setEnabled(enabled)
    
    def register_defaults(self, handlers: dict):
        """
        注册默认快捷键
        
        Args:
            handlers: 处理函数字典，如 {'open_file': self.open_file, 'print': self.print}
        """
        for action_name, handler in handlers.items():
            if action_name in self.DEFAULT_SHORTCUTS:
                key_seq = self.DEFAULT_SHORTCUTS[action_name]
                self.register(key_seq, handler)
    
    def get_shortcut_text(self, action_name: str) -> str:
        """获取快捷键显示文本"""
        return self.DEFAULT_SHORTCUTS.get(action_name, '')
