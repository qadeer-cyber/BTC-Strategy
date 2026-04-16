#!/usr/bin/env python3
from setuptools import setup, find_packages

APP_NAME = 'PolyCopilot'
APP_VERSION = '1.0.0'
APP_AUTHOR = 'PolyCopilot'
APP_DESCRIPTION = 'PolyMarket Copy Trading Desktop Application'
PYTHON_VERSION = '3.7'

setup(
    name=APP_NAME,
    version=APP_VERSION,
    author=APP_AUTHOR,
    description=APP_DESCRIPTION,
    packages=find_packages(),
    install_requires=[
        'requests>=2.25.1,<2.26',
    ],
    python_requires=f'>={PYTHON_VERSION}',
    entry_points={
        'console_scripts': [
            'polycopilot=polycopilot.main:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: MacOS :: MacOS X (10.13+)',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)