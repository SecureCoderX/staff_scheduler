from setuptools import setup, find_packages

setup(
    name="staff_scheduler",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.6.0",
        "pyinstaller>=6.11.0"
    ],
    python_requires=">=3.8",
    author="Your Name",
    description="A staff scheduling application",
    entry_points={
        "console_scripts": [
            "staff-scheduler=src.main:main",
        ],
    },
)
