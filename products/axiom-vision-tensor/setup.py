from setuptools import setup, find_packages

setup(
    name="axiom-vision-tensor",
    version="1.0.0",
    packages=find_packages(include=["axiom_vision", "axiom_vision.*"]),
    install_requires=[
        "numpy>=1.22.0",
        "pillow>=9.0.0",
    ],
    extras_require={
        "win32": ["pywin32>=305"],
    },
    entry_points={
        "console_scripts": [
            "axiom-vision=axiom_vision.cli:main",
        ],
    },
    python_requires=">=3.8",
)
