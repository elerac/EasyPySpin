from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="EasyPySpin",
    version="2.0.0",
    description="cv2.VideoCapture like wrapper for FLIR Spinnaker SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/elerac/EasyPySpin",
    author="Ryota Maeda",
    author_email="maeda.ryota.elerac@gmail.com",
    license="MIT",
    entry_points={"console_scripts": ["EasyPySpin= EasyPySpin.command_line:main"]},
    packages=find_packages(),
)
