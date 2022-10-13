import io
import re

from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()

# source: https://stackoverflow.com/a/39671214/1933315
__version__ = re.search(
    r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
    io.open("alph/__version__.py", encoding="utf_8_sig").read(),
).group(1)

setup(
    version=__version__,
    name="alph",
    description="alph",
    author="Uros Rapajic",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/connectedcompany/alph",
    license_files=["LICENSE"],
    install_requires=[
        "altair>=4.1.0",
        "networkx>=2.6.3",
        "pandas<1.5.0",  # 1.5.0 causes ValueError: columns cannot be a set when plotting altair facets
        "pygraphviz>=1.10",
        "scikit-network>=0.27.1",
        # "cython fa2 @ git+https://github.com/connectedcompany/forceatlas2.git@random-seed",
    ],
    python_requires=">=3.8",
    packages=find_packages(exclude=["*tests.*", "*examples.*"]),
)
