# setup.py
from setuptools import setup
from Cython.Build import cythonize
from distutils.extension import Extension

extensions = [
    Extension("app_cython", ["app_cython.pyx"])
]

setup(
    name='app_cython',
    ext_modules=cythonize(extensions),
)