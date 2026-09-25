# -*- mode: python ; coding: utf-8 -*-
"""
Especificación de PyInstaller para compilar SmartBreak en un ejecutable nativo de Windows.
Empaqueta MediaPipe, PyQt6, OpenCV, pystray y los assets gráficos sin consola (--noconsole).
"""

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

project_root = Path(SPECPATH).parent.resolve()
assets_dir = project_root / "assets"

# Recolectar archivos binarios y grafos de MediaPipe
mediapipe_datas = collect_data_files('mediapipe')

models_dir = project_root / "models"

datas = [
    (str(assets_dir), "assets"),
    (str(models_dir / "pose_landmarker_lite.task"), "models"),
] + mediapipe_datas

hiddenimports = [
    'mediapipe',
    'pystray',
    'pystray._win32',
    'PIL',
    'PIL.Image',
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'cv2',
    'numpy',
    'win32gui',
    'win32con',
    'win32api',
    'win32event',
    'pygrabber',
    'pygrabber.dshow_graph',
    'comtypes',
    'config',
    'config.settings',
    'config.autostart',
    'core',
    'core.orchestrator',
    'core.timer_service',
    'core.activity_monitor',
    'core.tray_controller',
    'core.vision_worker',
    'ui',
    'ui.lock_window',
    'ui.config_dialog',
    'ui.status_dialog',
    'ui.video_canvas',
    'vision',
    'vision.exercise_catalog',
    'vision.exercise_verifier',
    'vision.pose_detector',
] + collect_submodules('mediapipe')

a = Analysis(
    [str(project_root / 'run.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'torch', 'torchvision', 'scipy', 'pandas', 'IPython'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Configuración Onedir (Recomendada para MediaPipe por carga dinámica de modelos .binarypb)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SmartBreak',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Modo silencioso sin consola (--noconsole)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(assets_dir / 'icon.ico'),
)

import mediapipe
mediapipe_dir = os.path.dirname(mediapipe.__file__)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    Tree(mediapipe_dir, prefix='mediapipe'),
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SmartBreak',
)
