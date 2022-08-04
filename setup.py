from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="cotat",
    version="0.1.0",
    author="Cornell Covid Modeling Team",
    author_email="hwr26@cornell.edu",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cornell-covid-modeling/cotat",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "numpy>=1.20",
        "pandas>=1.2",
        "networkx>=2.5",
        "bokeh>=2.3"
    ],
    extras_require={
        "dev": ['pytest>=5',
                'mock>=3',
                'coverage>=4.5',
                'tox>=3',
                "flake8>=3.9"]
    },
    python_requires='>=3.5',
)