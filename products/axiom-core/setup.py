from setuptools import setup, find_packages

setup(
    name="axiom-core",
    version="2.0.0",
    packages=find_packages(include=["axiom_core", "axiom_core.*"]),
    install_requires=[
        "pydantic>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "axiomc = axiom_core.compiler:main",
            "axiom-hud = axiom_core.telemetry_hud:main",
        ]
    },
    package_data={
        "axiom_core": ["../bin/*", "../include/axiom/*"],
    },
    include_package_data=True,
    python_requires=">=3.8",
)
