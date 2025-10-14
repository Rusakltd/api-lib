from setuptools import setup, find_packages

setup(
    name="api_lib",
    version="0.12",
    packages=find_packages(),  # <- добавлена запятая
    install_requires=[
        "requests",  # <- в кавычках
        "pytz",      # <- в кавычках
    ]
)