from setuptools import setup, find_packages

setup(
    name='EasyPySpin',
    version='1.2.0',
    description='cv2.VideoCapture like wrapper for FLIR Spinnaker SDK',
    url='https://github.com/elerac/EasyPySpin',
    author='Ryota Maeda',
    author_email='maeda.ryota.elerac@gmail.com',
    license='MIT',
    entry_points={'console_scripts': ['EasyPySpin= EasyPySpin.command_line:main']},
    packages=find_packages()
)
