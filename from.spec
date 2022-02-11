# -*- mode: python -*-

block_cipher = None


a = Analysis(['from', 'PyQt5', 'import', 'uic,', 'QtCore,', 'QtGui,', 'QtWidgets.py'],
             pathex=['C:\\Users\\RobinWeber\\Box Sync\\Documents\\Eclipse-workspace\\MSLibRepSniffer'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='from',
          debug=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='from')
