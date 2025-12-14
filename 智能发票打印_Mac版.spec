# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['InvoiceMaster.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('qr1.jpg', '.'), 
        ('qr2.jpg', '.'), 
        ('src/core/license_manager.py', 'src/core'),
        ('icon_1x1_l.png', '.'),
        ('icon_1x1_p.png', '.'),
        ('icon_1x2_l.png', '.'),
        ('icon_1x2_p.png', '.'),
        ('icon_2x2_l.png', '.'),
        ('icon_2x2_p.png', '.'),
    ],
    hiddenimports=[
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
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='智能发票打印_Mac版',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['logo.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='智能发票打印_Mac版',
)
app = BUNDLE(
    coll,
    name='智能发票打印_Mac版.app',
    icon='logo.icns',
    bundle_identifier=None,
)
