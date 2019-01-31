#!/usr/bin/env python

from distutils.core import setup

setup(
    name="pswd-snitch",
    version="1.0",
    description="Password manager, that hides its content within PNG images",
    url="https://github.com/karol-gruszczyk/pswd-snitch",
    author="Karol Gruszczyk",
    author_email="karol.gruszczyk@gmail.com",
    license="MIT",
    packages=["crypto", "password_manager", "components"],
    install_requires=["cryptography", "Pillow", "pyperclip", "urwid"],
)
