#  Copyright 2022 IBM Corp. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from setuptools import setup, find_packages

requires = [
    'requests>=2'
]

setup(
    name='hodarchive',
    version='1.0.0',
    description='Environmental Intelligence Suite - (Weather) History on Demand SDK',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='IBM',
    author_email='twcapi@us.ibm.com',
    license='Apache License 2.0',
    url='https://github.com/ibm/hod-archive-sdk-python',
    packages=find_packages(exclude=['sampledata*']),
    python_requires='>=3.7',
    install_requires=requires,
    project_urls={
        'Documentation': 'https://ibm.co/2YEa7Q1',
        'Source': 'https://github.com/IBM/hod-archive-sdk-python'
    }
)
