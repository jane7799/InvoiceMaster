# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['InvoiceMaster.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('qr1.jpg', '.'), 
        ('qr2.jpg', '.'), 
        ('license_manager.py', '.'),
        ('icon_1x1_l.png', '.'),
        ('icon_1x1_p.png', '.'),
        ('icon_1x2_l.png', '.'),
        ('icon_1x2_p.png', '.'),
        ('icon_2x2_l.png', '.'),
        ('icon_2x2_p.png', '.'),
    ],
    hiddenimports=[],
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
