# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name='ctparse',
    version='0.0.1',
    description='Parse natural language time expressions into structured ones',
    long_description=long_description,
    url='https://github.com/comtravo/ctparse',
    author='Comtravo',
    author_email='sebastian.mika@comtravo.com',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',
        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Linguistic',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6'
    ],
    keywords='time parsing natural language',
    packages=find_packages(),

    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    #
    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['numpy>=1.14.0,<2.0.0',
                      'python-dateutil>=2.6.1,<3.0.0',
                      'regex>=2018.2.8',
                      'scikit-learn>=0.19.1,<1.0.0',
                      'scipy>=1.0.0,<2.0.0',
                      'tqdm>=4.19.5,<5.0.0'],
    extras_require={  # Optional
        'dev': [],
        'test': ['pytest', 'pytest-coverage', 'pytest-flake8'],
    },

    # If there are data files included in your packages that need to be
    # installed, specify them here.
    #
    # If using Python 2.6 or earlier, then these have to be included in
    # MANIFEST.in as well.
    package_data={
        # 'sample': ['package_data.dat'],
    },
    # data_files=[],
    entry_points={},
    project_urls={
    },
)
