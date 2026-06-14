# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('templates', 'templates'), ('static', 'static'), ('moodie_model.pkl', '.'), ('moodie_labels.pkl', '.')],
    hiddenimports=['food_data', 'sklearn.ensemble', 'sklearn.preprocessing', 'sklearn.compose', 'sklearn.pipeline', 'sklearn.utils._typedefs', 'sklearn.utils._cython_blas', 'sklearn.neighbors._typedefs', 'sklearn.neighbors._partition_nodes', 'sklearn.tree._utils'],
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
    a.binaries,
    a.datas,
    [],
    name='Moodie_Foodie_Final',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
