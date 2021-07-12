# setup.py
from setuptools import setup, find_packages

setup(
    name='VectorGym',
    version='0.1.0',
    packages=['VectorGym'],
    license='MIT',
    packages=find_packages(),
    options={'bdist_wheel': {
        'universal': True
    }},
)
