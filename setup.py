import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="arqLogger",
    version="0.0.1b11",
    author="Franco Zanuso",
    author_email="francozanuso89@gmail.com",
    description="Python websocket logger for Arquant's Strategies.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'apscheduler>=3.0.0',
        'Twisted>=20.3.0',
        'autobahn>=20.6.2',
        'enum34>=1.1.6',
        "websocket-client>=0.54.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Software Development"
    ],
)
