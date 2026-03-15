from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="term-agent",
    version="0.1.1",
    author="TermAgent",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=requirements,
    extras_require={
        "dev": ["setuptools", "wheel", "twine"]
    },
    entry_points={
        "console_scripts": [
            "term=term_agent.main:main",
        ],
    },
)
