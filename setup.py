from setuptools import setup, find_packages

import pathlib


here = pathlib.Path(__file__).parent.resolve()

# Get long version of description from README file
long_description = (here / 'README.md').read_text(encoding='utf-8')


dev_requirements = [
    'pexpect>=4.8.0',
    'autopep8>=1.5.4',
    'flake8>=3.8.4',
    'pytest>=6.2.1',
]

publish_requirements = dev_requirements + ['twine>=3.2.0']


setup(
    name='http_logging',
    version='0.1.0',
    description='Non-blocking HTTP handler for Python `logging` with local '
                'SQLite buffer/cache.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/hacktlib/py-async-http-logging/wiki',
    author='Hackt.app',
    author_email='opensource@hackt.app',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
    ],
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    python_requires='>=3.6, <4',
    install_requires=[
        'python-logstash-async>=2.2.0',
        'requests>=2.25.1',
    ],
    extras_require={
        'dev': dev_requirements,
        'pub': publish_requirements,
    },
    project_urls={
        'Bug Reports': 'https://github.com/hacktlib/py-async-http-logging/issues',
        'Say Thanks!': 'http://lib.hackt.app',
        'Source': 'https://github.com/hacktlib/py-async-http-logging/',
    },
)
