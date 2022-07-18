#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = []

setup_requirements = [
    "pytest-runner",
]

test_requirements = [
    "pytest",
]

setup(
    author="Sebastian Mika/Comtravo",
    author_email="sebastian.mika@comtravo.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    description="Parse natural language time expressions in python",
    install_requires=["python-dateutil>=2.7.3,<3.0.0", "regex>=2018.6.6", "tqdm>=4.23.4,<5.0.0"],
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="ctparse time parsing natural language",
    name="ctparse",
    packages=find_packages(include=["ctparse*"]),
    package_dir={"ctparse": "ctparse"},
    package_data={"ctparse": ["models/model.pbz", "py.typed"]},
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/comtravo/ctparse",
    version="0.3.2",
    zip_safe=False,
)
