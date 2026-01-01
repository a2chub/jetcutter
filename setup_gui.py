"""
JetCutter GUI - py2app configuration

macOS .app バンドルをビルドするための設定。

Usage:
    python setup_gui.py py2app

Output:
    dist/JetCutter.app
"""

from setuptools import setup

APP = ["src/jetcutter/gui/app.py"]

DATA_FILES = [
    ("config", ["config/settings.yaml", "config/fillers.yaml"]),
]

OPTIONS = {
    "argv_emulation": False,
    "packages": [
        "jetcutter",
        "PySimpleGUI",
        "pydub",
        "faster_whisper",
        "pydantic",
        "pydantic_settings",
        "yaml",
        "ctranslate2",
        "huggingface_hub",
        "tokenizers",
    ],
    "includes": [
        "tkinter",
    ],
    "excludes": [
        "matplotlib",
        "numpy.testing",
        "scipy",
    ],
    "plist": {
        "CFBundleName": "JetCutter",
        "CFBundleDisplayName": "JetCutter",
        "CFBundleIdentifier": "com.jetcutter.app",
        "CFBundleVersion": "0.1.0",
        "CFBundleShortVersionString": "0.1.0",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "10.15",
        "NSRequiresAquaSystemAppearance": False,
        "CFBundleDocumentTypes": [
            {
                "CFBundleTypeName": "Video File",
                "CFBundleTypeExtensions": ["mp4", "mov", "avi", "mkv", "webm"],
                "CFBundleTypeRole": "Viewer",
            }
        ],
    },
}

setup(
    name="JetCutter",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
