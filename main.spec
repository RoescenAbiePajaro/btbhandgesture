# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files
import os

# Collect MediaPipe model and asset files
mediapipe_datas = collect_data_files(
    'mediapipe',
    includes=['**/*.binarypb', '**/*.tflite', '**/*.json', '**/*.txt']
)

# Add header and guide folders as separate data entries
header_files = [(os.path.join('header', f), 'header') for f in os.listdir('header')] if os.path.exists('header') else []
guide_files = [(os.path.join('guide', f), 'guide') for f in os.listdir('guide')] if os.path.exists('guide') else []

# Make sure icon files are properly included
icon_files = [(os.path.join('icon', f), 'icon') for f in os.listdir('icon')] if os.path.exists('icon') else []

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=mediapipe_datas + header_files + guide_files + icon_files + 
          [('VirtualPainter.py', '.'), 
           ('HandTrackingModule.py', '.'),
           ('KeyboardInput.py', '.'),
           ('SizeAdjustmentWindow.py', '.'),
           ('icon/icons.png', 'icon'),
           ('icon/logo.png', 'icon'),
           ('size_config.json', '.'), 
           ],  # Added icons.png explicitly

    hiddenimports=['VirtualPainter', 'HandTrackingModule', 'KeyboardInput','SizeAdjustmentWindow', 'cv2', 'numpy', 'PIL', 'tkinter'],
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
    name='BeyondTheBrush',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # set to True if you want console logs
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon/app.ico',  # Only specify one icon here
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BeyondTheBrush',
    icon='icon/app.ico',  # Only specify one icon here
)






