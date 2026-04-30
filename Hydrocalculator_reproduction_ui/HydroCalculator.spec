# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\APPS\\python\\projects\\cg-model-reproduction\\Hydrocalculator_reproduction_ui\\launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\APPS\\python\\projects\\cg-model-reproduction\\Hydrocalculator_reproduction_ui\\index.html', 'Hydrocalculator_reproduction_ui'), ('D:\\APPS\\python\\projects\\cg-model-reproduction\\Hydrocalculator_reproduction_ui\\styles.css', 'Hydrocalculator_reproduction_ui'), ('D:\\APPS\\python\\projects\\cg-model-reproduction\\Hydrocalculator_reproduction_ui\\app.js', 'Hydrocalculator_reproduction_ui'), ('D:\\APPS\\python\\projects\\cg-model-reproduction\\Hydrocalculator_reproduction_ui\\hydrocalc-core.js', 'Hydrocalculator_reproduction_ui'), ('D:\\APPS\\python\\projects\\cg-model-reproduction\\Hydrocalculator_reproduction_ui\\README.md', 'Hydrocalculator_reproduction_ui'), ('D:\\APPS\\python\\projects\\cg-model-reproduction\\Hydrocalculator_full-offline_version1-04\\HydroCalculator_104_unpacked\\resources\\images\\icona_hcalc.jpg', 'Hydrocalculator_full-offline_version1-04\\HydroCalculator_104_unpacked\\resources\\images')],
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
    a.binaries,
    a.datas,
    [],
    name='HydroCalculator',
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
