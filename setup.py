#!/usr/bin/env python

from setuptools import setup, find_packages
import sys
import os.path

if sys.version_info < (3, 7, 0):
    sys.stderr.write("ERROR: You need Python 3.7 or later to use exif2findertags.\n")
    exit(1)

# we'll import stuff from the source tree, let's ensure is on the sys path
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

# read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

about = {}
with open(
    os.path.join(this_directory, "exif2findertags", "_version.py"),
    mode="r",
    encoding="utf-8",
) as f:
    exec(f.read(), about)

setup(
    name="exif2findertags",
    version=about["__version__"],
    description="Read exif metadata from images with exiftool and write to MacOS Finder keywords",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Rhet Turnbull",
    author_email="rturnbull+git@gmail.com",
    url="https://github.com/RhetTbull/exif2findertags",
    project_urls={"GitHub": "https://github.com/RhetTbull/exif2findertags"},
    download_url="https://github.com/RhetTbull/exif2findertags",
    packages=find_packages(exclude=["tests", "utils"]),
    license="License :: OSI Approved :: MIT License",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: MacOS X",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=[
        "osxmetadata>=0.99.33",
        "click>=8.0",
        "yaspin>=2.1.0",
        "cloup>=0.11.0",
        "textx>=2.3.0",
        "pathvalidate>=2.4.1",
        "rich>=10.9.0",
    ],
    python_requires=">=3.7",
    entry_points={"console_scripts": ["exif2findertags=exif2findertags.cli:cli"]},
    include_package_data=True,
)
