# -*- coding:utf-8 -*-
import re
import os
try:
    from setuptools import setup, find_packages
except:
    from distutils.core import setup


def get_version(package):
    """
    Return package version as listed in `__version__` in `__init__.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    mth = re.search("__version__\s?=\s?['\"]([^'\"]+)['\"]", init_py)
    if mth:
        return mth.group(1)
    else:
        raise RuntimeError("Cannot find version!")


def install_requires():
    """
    Return requires in requirements.txt
    :return:
    """
    try:
        with open("requirements.txt") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except OSError:
        return []

try:
    LONG_DESCRIPTION = open("README.rst").read()
except UnicodeDecodeError:
    LONG_DESCRIPTION = open("README.rst", encoding="utf-8").read()


setup(
    name="async-downloader",
    version=get_version("async_downloader"),
    description="mutil file download from custom sources. ",
    long_description=LONG_DESCRIPTION,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
    ],
    entry_points={
        'console_scripts': [
            'a-download = async_downloader:main',
        ],
    },
    keywords="download async",
    author="cn",
    author_email="cnaafhvk@foxmail.com",
    url="https://www.github.com/ShichaoMa/async-downloader",
    license="MIT",
    packages=find_packages(),
    install_requires=install_requires(),
    include_package_data=True,
    zip_safe=True,
)
