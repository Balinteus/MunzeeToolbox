import os
import PyInstaller.__main__

image_folder = "img" + os.pathsep + "img"

PyInstaller.__main__.run(
    [
        "main.py",
        "--name", "QR-Signer",
        "--onefile",
        "--windowed",
        "--add-binary", image_folder,
        "--icon", "img/icon.ico",
    ]
)
