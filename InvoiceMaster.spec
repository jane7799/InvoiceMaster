# InvoiceMaster 打包配置
# 用于创建 Windows 独立可执行文件

block_cipher = None

a = Analysis(
    ['InvoiceMaster.py'],
    pathex=[],
    binaries=[],
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
