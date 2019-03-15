#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

install_requires = [
    'click>=3.3,<7',
    'keyring==8.7',
    'parsedatetime>=2.4,<3',
    'python-dateutil>=2.4.1,<3',
    'requests>=2.4.3,<3.0',
    'arrow>=0.5.4,<0.8',
    'termcolor==1.1.0',
    'six>=1.9.0',
]

tests_require = [
    'coverage==4.1',
    'httpretty==0.8.14',
    'mock==1.3.0',
    'pytest==4.3.1',
]

setup_requires = [
    'bumpversion==0.5.3',
    'flake8==2.6.0',
    'pytest-runner',
    'wheel==0.29.0',
]

setup(
    name='pygray',
    version='0.9.4',
    description="Graylog command line interface (pygray fork).",
    long_description=readme + '\n\n' + history,
    author="Joao Marcus Christ",
    author_email='joaoma@gmail.com',
    url='https://github.com/joaomarcusc/pygray',
    packages=[
        'pygray',
    ],
    package_dir={'pygray':
                 'pygray'},
    entry_points={
        'console_scripts': [
            'pygray=pygray.cli:run'
        ]
    },
    include_package_data=True,
    install_requires=install_requires,
    setup_requires=setup_requires,
    license="Apache Software License 2.0",
    zip_safe=False,
    keywords='pygray',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    test_suite='tests',
    tests_require=tests_require
)
