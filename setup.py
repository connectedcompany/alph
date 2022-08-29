from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()
import io
import re

# source: https://stackoverflow.com/a/39671214/1933315
__version__ = re.search(
    r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
    io.open("gralt/__init__.py", encoding="utf_8_sig").read(),
).group(1)

config = {
    "version": __version__,
    "name": "gralt",
    "description": "gralt",
    "author": "connectedcompany.io",
    "long_description": long_description,
    "long_description_content_type": "text/markdown",
    "url": "https://github.com/connectedcompany/gralt",
    #'download_url': 'Where to download it.',
    #'author_email': 'My email.',
    "install_requires": [
        "altair>=4.1.0",
        "fa2 @ git+https://github.com/connectedcompany/forceatlas2.git@random-seed",
        "networkx>=2.6.3",
        "pandas>=1.1.5",
    ],
    "python_requires": ">=3.7",
    "packages": find_packages(),
}

setup(**config)
