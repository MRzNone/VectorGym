# setup.py
from setuptools import setup
from os import path
from version import VERSION

# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='VectorGym',
    version=VERSION,
    packages=['VectorGym'],
    license='MIT',
    description='Simple multiprocess tool for gym environments',
    author='Weihao Zeng',
    author_email="whzeng98@gmail.com",
    url='https://github.com/MRzNone/VectorGym',
    keywords=['gym', 'multiprocess', 'parallel', 'simple'],
    download_url=
    F'https://github.com/MRzNone/VectorGym/archive/refs/tags/v{VERSION}.tar.gz',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'numpy',
        'gym',
        'dill',
    ],
    options={'bdist_wheel': {
        'universal': True
    }},
    classifiers=[
        'Development Status :: 3 - Alpha',  # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Intended Audience :: Developers',  # Define that your audience are developers
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',  # Again, pick a license
        'Programming Language :: Python :: 3',  #Specify which pyhton versions that you want to support
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
