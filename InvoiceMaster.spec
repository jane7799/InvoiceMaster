# InvoiceMaster 打包配置
# 用于创建 Windows 独立可执行文件
import os
import sys
import glob

block_cipher = None

# 收集 pyzbar DLL 依赖
pyzbar_binaries = []
try:
    import pyzbar
    pyzbar_dir = os.path.dirname(pyzbar.__file__)
    
    # pyzbar 需要的 DLL 文件列表（包括所有可能的名称变体）
    dll_files = [
        'libiconv.dll', 
        'libiconv-2.dll',
        'libzbar-64.dll', 
        'libzbar-32.dll', 
        'libzbar.dll',
        'libzbar-0.dll',
        'zbar.dll',
    ]
    
    # 搜索 DLL 的多个可能位置
    search_paths = [
        pyzbar_dir,                                    # pyzbar 包目录
        os.path.join(pyzbar_dir, 'bin'),              # pyzbar/bin 目录
        os.path.join(sys.prefix, 'Library', 'bin'),   # Conda 环境
        os.path.join(sys.prefix, 'Scripts'),          # Python Scripts 目录
        os.path.join(sys.prefix, 'DLLs'),             # Python DLLs 目录
    ]
    
    # 如果有 CONDA_PREFIX 环境变量，也搜索那里
    conda_prefix = os.environ.get('CONDA_PREFIX')
    if conda_prefix:
        search_paths.append(os.path.join(conda_prefix, 'Library', 'bin'))
    
    found_dlls = set()
    for search_path in search_paths:
        if os.path.exists(search_path):
            for dll in dll_files:
                dll_path = os.path.join(search_path, dll)
                if os.path.exists(dll_path) and dll not in found_dlls:
                    found_dlls.add(dll)
                    # (源文件路径, 目标目录)
                    pyzbar_binaries.append((dll_path, 'pyzbar'))
                    print(f"[pyzbar] 找到 DLL: {dll_path}")
            
            # 同时收集所有 .dll 文件（以防遗漏）
            for pattern in ['*.dll']:
                for dll_path in glob.glob(os.path.join(search_path, pattern)):
                    dll_name = os.path.basename(dll_path).lower()
                    if ('zbar' in dll_name or 'iconv' in dll_name) and dll_name not in found_dlls:
                        found_dlls.add(dll_name)
                        pyzbar_binaries.append((dll_path, 'pyzbar'))
                        print(f"[pyzbar] 额外找到 DLL: {dll_path}")

    if not pyzbar_binaries:
        print("[警告] 未找到 pyzbar DLL 文件，二维码功能可能无法使用")
        print(f"[警告] 已搜索路径: {search_paths}")
except ImportError:
    print("[警告] pyzbar 未安装")

# 收集 OpenCV DLL 依赖
cv2_binaries = []
try:
    import cv2
    cv2_dir = os.path.dirname(cv2.__file__)
    for f in os.listdir(cv2_dir):
        if f.endswith('.dll'):
            cv2_binaries.append((os.path.join(cv2_dir, f), 'cv2'))
            print(f"[cv2] 找到 DLL: {f}")
    if not cv2_binaries:
        print("[警告] OpenCV 目录中未找到 DLL 文件")
except ImportError:
    print("[警告] OpenCV (cv2) 未安装")

# 检测是使用 PyQt6 还是 PyQt5
qt_impl = 'PyQt6'
try:
    import PyQt6
except ImportError:
    try:
        import PyQt5
        qt_impl = 'PyQt5'
    except ImportError:
        pass

print(f"[*] PyInstaller spec: 检测到 Qt 实现为 {qt_impl}")

# 将动态检测到的 Qt 隐藏导入加入列表
qt_hidden_imports = [
    f'{qt_impl}.QtCore',
    f'{qt_impl}.QtGui',
    f'{qt_impl}.QtWidgets',
    f'{qt_impl}.QtPrintSupport',
]
if qt_impl == 'PyQt6':
    qt_hidden_imports.append('PyQt6.sip')
else:
    try:
        import PyQt5.sip
        qt_hidden_imports.append('PyQt5.sip')
    except ImportError:
        qt_hidden_imports.append('sip')

a = Analysis(
    ['InvoiceMaster.py'],
    pathex=[],
    binaries=pyzbar_binaries + cv2_binaries,
    datas=[
        ('src/core/license_manager.py', 'src/core'),
        ('src/utils/startup_check.py', 'src/utils'),
        ('runtime_hook.py', '.'),
        ('qr1.jpg', '.'),
        ('qr2.jpg', '.'),
        ('icon_1x1_l.png', '.'),
        ('icon_1x1_p.png', '.'),
        ('icon_1x2_l.png', '.'),
        ('icon_1x2_p.png', '.'),
        ('icon_2x2_l.png', '.'),
        ('icon_2x2_p.png', '.'),
    ],
    hiddenimports=qt_hidden_imports + [
        'pandas',
        'openpyxl',
        'fitz',
        'requests',
        'cv2',
        'pyzbar',
        'pyzbar.pyzbar',
        'json',
        'sqlite3',
        'concurrent.futures',
        'src.core.database', 'src.core.workers', 'src.core.pdf_engine', 'src.core.print_engine',
        'src.core.invoice_helper', 'src.core.license_manager',
        'src.utils.log_manager', 'src.utils.icons', 'src.utils.config', 'src.utils.utils',
        'src.utils.startup_check', 'src.utils.qt_compat',
        'src.themes.theme_manager',
        'src.ui.main_window', 'src.ui.dialogs', 'src.ui.settings_dialog',
        'src.ui.statistics_dialog', 'src.ui.widgets', 'src.ui.preview',
        'src.ui.print_preview_dialog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='智能发票打印助手',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.ico' if os.path.exists('logo.ico') else None,
)
