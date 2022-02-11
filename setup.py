from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages = [], excludes = [])

import sys
base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('MSLibRepSniffer_GUI_main.py', base=base, targetName = 'MSLibRep')
]

setup(name='MSLibRepSniffer',
      version = '0.1',
      description = 'Replicate detector for mass spectral libraries',
      options = dict(build_exe = buildOptions),
      executables = executables)
