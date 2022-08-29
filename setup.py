from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()
import io
import re

# source: https://stackoverflow.com/a/39671214/1933315
__version__ = re.search(
    r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
    io.open("alph/__init__.py", encoding="utf_8_sig").read(),
).group(1)

config = {
    "version": __version__,
    "name": "alph",
    "description": "alph",
    "author": "connectedcompany.io",
    "long_description": long_description,
    "long_description_content_type": "text/markdown",
    "url": "https://github.com/connectedcompany/alph",
    #'download_url': 'Where to download it.',
    #'author_email': 'My email.',
    "install_requires": [
        "altair>=4.1.0",
        "fa2 @ git+https://github.com/connectedcompany/forceatlas2.git@random-seed",
        "networkx>=2.6.3",
        "numpy>=1.22.4",
        "pandas>=1.3.5",
    ],
    "python_requires": ">=3.8",
    "packages": find_packages(),
}

setup(**config)
