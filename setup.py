#!/usr/bin/env python

VERSION = "1.0.0"

from setuptools import setup, find_packages

with open("requirements.txt") as f:
  install_requires = f.read().splitlines()

tests_require = [
    "pytest",
]

setup(name="exio",
      version=VERSION,
      description="ex.io python api",
      long_description=open("README.md").read(),
      author="Jake Li",
      author_email="zyli5313@gmail.com",
      url="https://github.com/ex-io/exio-python",
      license="MIT",
      keywords=["exio, ex.io, exio-python", "exio-api", "BTC", "ETH", "bitcoin", "ethereum"],
      packages=find_packages(exclude=["tests"]),
      install_requires=install_requires,
      tests_require=tests_require,
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Intended Audience :: Developers",
          "Intended Audience :: Financial and Insurance Industry",
          "Intended Audience :: Information Technology",
          "Topic :: Software Development :: Libraries :: Python Modules",
          "License :: OSI Approved :: MIT License",
          "Programming Language :: Python :: 2",
      ],
      )
