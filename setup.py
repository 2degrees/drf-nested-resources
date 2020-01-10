##############################################################################
#
# Copyright (c) 2015-2020 2degrees Limited.
# All Rights Reserved.
#
# This file is part of drf-nested-resources
# <https://github.com/2degrees/drf-nested-resources>, which is subject to the
# provisions of the BSD at
# <http://dev.2degreesnetwork.com/p/2degrees-license.html>. A copy of the
# license should accompany this distribution. THIS SOFTWARE IS PROVIDED "AS IS"
# AND ANY AND ALL EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST
# INFRINGEMENT, AND FITNESS FOR A PARTICULAR PURPOSE.
#
##############################################################################

from os import path

from setuptools import find_packages
from setuptools import setup


_HERE = path.abspath(path.dirname(__file__))
_VERSION = open(path.join(_HERE, 'VERSION.txt')).readline().rstrip()
_README = open(path.join(_HERE, 'README.md')).read().strip()
_CHANGELOG = open(path.join(_HERE, 'CHANGELOG.md')).read().strip()
_LONG_DESCRIPTION = '\n\n'.join((_README, _CHANGELOG))


setup(
    name='drf-nested-resources',
    version=_VERSION,
    description='Support for nested routes in the Django REST Framework',
    long_description=_LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='https://pypi.python.org/pypi/drf-nested-resources',
    author='2degrees Limited',
    author_email='foss@2degreesnetwork.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries',
        ],
    keywords='',
    license='BSD (http://dev.2degreesnetwork.com/p/2degrees-license.html)',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    exclude_package_data={'': ['README.md', 'CHANGELOG.md']},
    install_requires=['djangorestframework >= 3.9.2', 'pyrecord >= 1.0rc2'],
    )
