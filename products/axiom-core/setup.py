from setuptools import setup, find_packages

setup(
    name="axiom-core",
    version="1.0.0",
    packages=find_packages(include=["axiom_core", "axiom_core.*"]),
    install_requires=[
        "pydantic>=2.0.0",
    ],
    package_data={
        "axiom_core": ["../bin/*", "../include/axiom/*"],
    },
    include_package_data=True,
    python_requires=">=3.8",
)
