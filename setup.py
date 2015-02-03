# -*- coding: utf-8 -*-
"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

import os
from distutils.sysconfig import get_python_inc, get_python_lib
import numpy
import platform
has_py2app = False
import gavi.vaex
try:
	import py2app.build_app
	has_py2app = True
except:
	pass

full_name = gavi.vaex.__full_name__
cmdclass = {}

if has_py2app:
	class my_py2app(py2app.build_app.py2app):
		"""hooks in post script to add in missing libraries and zip the content"""
		def run(self):
			py2app.build_app.py2app.run(self)
			#libQtWebKit.4.dylib
			#libQtNetwork.4.dylib
			libs = [line.strip() for line in """
			libLLVM-3.3.dylib
			libQtGui.4.dylib
			libQtCore.4.dylib
			libQtOpenGL.4.dylib
			libcrypto.1.0.0.dylib
			libssl.1.0.0.dylib
			libpng15.15.dylib
			libfreetype.6.dylib
			""".strip().splitlines()]

			libpath = "/Users/maartenbreddels/anaconda/lib"
			targetdir = 'dist/vaex.app/Contents/Resources/lib/'
			for filename in libs:
				path = os.path.join(libpath, filename)
				cmd = "cp %s %s" % (path, targetdir)
				print cmd
				os.system(cmd)

			libs = [line.strip() for line in """
			libpng15.15.dylib
			""".strip().splitlines()]
			targetdir = 'dist/vaex.app/Contents/Resources/'
			for filename in libs:
				#path = os.path.join(libpath, filename)
				cmd = "cp %s %s" % (path, targetdir)
				print cmd
				os.system(cmd)
			os.system("cd dist")
			zipname = "%s-osx.zip" % gavi.vaex.__clean_name__
			os.system("cd dist;rm %s" % zipname)
			os.system("cd dist;zip -r %s %s.app" % (zipname, gavi.vaex.__program_name__))
	cmdclass['py2app'] = my_py2app
			
from distutils.core import setup, Extension
numdir = os.path.dirname(numpy.__file__)

import sys 
sys.setrecursionlimit(10000)

APP = ["bin/vaex"]
DATA_FILES = []
if has_py2app:
	pass
	#DATA_FILES.append(["data", ["data/disk-galaxy.hdf5"]]) #, "data/Aq-A-2-999-shuffled-1percent.hdf5"]])
import glob

DATA_FILES.append(["", glob.glob("doc/*/*")])
OPTIONS = {'argv_emulation': False, 'excludes':[], 'resources':['python/gavi/icons'], 'matplotlib_backends':'-'}



include_dirs = []
library_dirs = []
libraries = []
defines = []
if "darwin" in platform.system().lower():
	extra_compile_args = ["-mfpmath=sse", "-O3", "-funroll-loops"]
else:
	#extra_compile_args = ["-mfpmath=sse", "-msse4", "-Ofast", "-flto", "-march=native", "-funroll-loops"]
	#extra_compile_args = ["-mfpmath=sse", "-msse4", "-Ofast", "-flto", "-funroll-loops"]
	extra_compile_args = ["-mfpmath=sse", "-O3", "-funroll-loops"]
	#extra_compile_args = ["-mfpmath=sse", "-msse4a", "-O3", "-funroll-loops"]
extra_compile_args.extend(["-std=c++0x"])

include_dirs.append(os.path.join(get_python_inc(plat_specific=1), "numpy"))
include_dirs.append(os.path.join(numdir, "core", "include"))

extensions = [
	Extension("gavifast", ["src/gavi.cpp"],
                include_dirs=include_dirs,
                library_dirs=library_dirs,
                libraries=libraries,
                define_macros=defines,
                extra_compile_args=extra_compile_args
                )
]

setup(
	name=gavi.vaex.__program_name__,
    app=APP,
    version=gavi.vaex.__release__,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    includes=["gavi", "md5"],
    ext_modules=extensions,
    package_data={'gavi': ['gavi/icons/*.png']},
    cmdclass=cmdclass
)

