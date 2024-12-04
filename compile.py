from sys import platform

import PyInstaller.__main__

args = [
    'gui_app.py',
    '--hidden-import=pyimg4',
    '--hidden-import=zeroconf',
    '--hidden-import=zeroconf._utils.ipaddress',
    '--hidden-import=zeroconf._handlers.answers',
    '--copy-metadata=pyimg4',
    '--onedir',
    '--noconfirm',
    '--name=QuietDaemon',
    '--icon=icon.png',
    '--optimize=2'
]

PyInstaller.__main__.run(args)

if platform == "darwin":
    # add --windowed arg for macOS
    args.append('--windowed')

PyInstaller.__main__.run(args)
