## setup.py build_ext --inplace
import sys
sys.argv.extend(["build_ext","--inplace"])

print("Importing setuptools...")
from setuptools import setup
print("[+] Done (setuptools import)\n")
print("Importing Cython...")
from Cython.Build import cythonize
print("[+] Done (Cython import)\n")
print("Importing Extension...")
from distutils.extension import Extension
print("[+] Done (Extension import)\n")

print("Compiling the program into Cython...\n\n###")
setup(
    name='Scraper',
    ext_modules=cythonize("Browser.pyx", 
                            language="c++", language_level=3),
    zip_safe=False,
    extra_compile_args=["-O3"]
)
print("###\n\n[+] Done (Compilation)\n")