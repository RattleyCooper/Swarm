import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Swarm",
    version="0.0.1",
    author="py-am-i",
    author_email="duckpuncherirl@gmail.com",
    description="Swarm is a strategy rouge-like space simulator game written with `pygame/python3`.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    install_requires=[
        'pygame'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
