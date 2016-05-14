#!/usr/bin/env python

import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand

required_packages = ['pyparsing==2.1.1']
if sys.version_info[:2] == (2, 6):
    required_packages.append('argparse')
    required_packages.append('ordereddict')


class PyTestCommand(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

setup(
    name='pyhocon',
    version='0.3.28',
    description='HOCON parser for Python',
    long_description='pyhocon is a HOCON parser for Python. Additionally we provide a tool (pyhocon) to convert any HOCON '
                     'content into json, yaml and properties format.',
    keywords='hocon parser',
    license='Apache License 2.0',
    author='Francois Dang Ngoc',
    author_email='francois.dangngoc@gmail.com',
    url='http://github.com/chimpler/pyhocon/',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    packages=[
        'pyhocon',
    ],
    install_requires=required_packages,
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'pyhocon=pyhocon.tool:main'
        ]
    },
    test_suite='tests',
    cmdclass={
        'test': PyTestCommand
    }
)
