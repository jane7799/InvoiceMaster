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

a = Analysis(
    ['InvoiceMaster.py'],
    pathex=[],
    binaries=pyzbar_binaries,
    datas=[
        ('src/core/license_manager.py', 'src/core'),
        ('qr1.jpg', '.'),
        ('qr2.jpg', '.'),
        ('icon_1x1_l.png', '.'),
        ('icon_1x1_p.png', '.'),
        ('icon_1x2_l.png', '.'),
        ('icon_1x2_p.png', '.'),
        ('icon_2x2_l.png', '.'),
        ('icon_2x2_p.png', '.'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtPrintSupport',
        'pandas',
        'openpyxl',
        'fitz',
        'requests',
        'cv2',
        'pyzbar',
        'pyzbar.pyzbar',
        'src.core.database', 'src.core.workers', 'src.core.pdf_engine', 'src.core.print_engine',
        'src.core.invoice_helper', 'src.core.license_manager', 
        'src.utils.log_manager', 'src.utils.icons', 'src.utils.config', 'src.utils.utils',
        'src.themes.theme_manager',
        'src.ui.main_window', 'src.ui.dialogs', 'src.ui.settings_dialog', 
        'src.ui.statistics_dialog', 'src.ui.widgets', 'src.ui.preview'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
