from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ctparse',
    version='0.0.1',
    description='Parse natural language time expressions into structured ones',
    long_description=long_description,
    url='https://github.com/comtravo/ctparse',
    author='Comtravo',
    author_email='sebastian.mika@comtravo.com',
    maintainer='Sebastian Mika',
    maintainer_email='sebastian.mika@comtravo.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Linguistic',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6'
    ],
    keywords='time parsing natural language',
    packages=['ctparse'],
    package_dir={'ctparse': 'ctparse'},
    package_data={'ctparse': ['models/model.pbz']},
    install_requires=['numpy>=1.14.0,<2.0.0',
                      'python-dateutil>=2.6.1,<3.0.0',
                      'regex>=2018.2.8',
                      'scikit-learn>=0.19.1,<1.0.0',
                      'scipy>=1.0.0,<2.0.0',
                      'tqdm>=4.19.5,<5.0.0'],
    extras_require={
        'dev': [],
        'test': ['pytest', 'pytest-coverage', 'pytest-flake8'],
    },
    entry_points={},
    project_urls={},
)
