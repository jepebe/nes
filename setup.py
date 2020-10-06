#!/usr/bin/env python3

import os
import re
from setuptools import setup

setup(
    version="0.0.0",
    name="nes",
    packages=["nes"],
    description="NES emulator",
    long_description="NES emulator",
    long_description_content_type="text/markdown",
    author="JP Balabanian",
    license="MIT",
    keywords="nes,emulator",
    entry_points={
        "console_scripts": [
            "nes = nes:main",
        ],
    },
    test_suite="tests",
    tests_require=["pytest"],
)
