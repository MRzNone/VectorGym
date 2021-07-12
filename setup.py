# setup.py
from setuptools import setup

setup(
    name='VectorGym',
    version='0.1.0',
    packages=['VectorGym'],
    license='MIT',
    options={'bdist_wheel': {
        'universal': True
    }},
)
