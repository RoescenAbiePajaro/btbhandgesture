# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files

# ----------------------------------------------------------------------
# 1. Collect every file you need (models, icons, headers, guides …)
# ----------------------------------------------------------------------
mediapipe_datas = collect_data_files(
    'mediapipe',
    includes=['**/*.binarypb', '**/*.tflite', '**/*.json', '**/*.txt']
)

def _collect_folder(folder):
    """Return a list of (src, dest) tuples for a folder, preserving its name."""
    if not os.path.isdir(folder):
        return []
    return [(os.path.join(folder, f), folder) for f in os.listdir(folder)]

header_files = _collect_folder('header')
guide_files  = _collect_folder('guide')
icon_files   = _collect_folder('icon')

# ----------------------------------------------------------------------
# 2. Analysis – ONEFILE mode + all datas
# ----------------------------------------------------------------------
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=(
        mediapipe_datas +
        header_files + guide_files + icon_files +
        [
            ('VirtualPainter.py',        '.'),
            ('HandTrackingModule.py',    '.'),
            ('KeyboardInput.py',         '.'),
            ('SizeAdjustmentWindow.py',  '.'),
            ('track_click.py',           '.'),
            ('icon/icons.png',           'icon'),
            ('icon/logo.png',            'icon'),
            ('size_config.json',         '.'),
        ]
    ),
    hiddenimports=[
        'VirtualPainter', 'HandTrackingModule', 'KeyboardInput',
        'SizeAdjustmentWindow', 'track_click',
        'cv2', 'numpy', 'PIL', 'tkinter'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# ----------------------------------------------------------------------
# 3. Build a **single executable** (no external _internal folder)
# ----------------------------------------------------------------------
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],                     # no extra options here
    name='BeyondTheBrush',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # set True only for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon/app.ico',
    # ---- ONEFILE is the key ------------------------------------------------
    onefile=True,           # <── everything packed into ONE .exe
)

# ----------------------------------------------------------------------
# 4. (Optional) If you ever need COLLECT again, keep the same icon
# ----------------------------------------------------------------------
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.datas,
#     strip=False,
#     upx=True,
#     name='BeyondTheBrush',
#     icon='icon/app.ico',
# )