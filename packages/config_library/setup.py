from setuptools import setup, find_packages

import json
import os


if __name__ == '__main__':
    setup(
        name='alumnihub-config-library',
        version='0.0.1',
        package_dir={'': 'src'},
        packages=find_packages('src', include=[
            '*config_library*'
        ]),
        install_requires=[
            'pydantic',
            'pydantic_settings',
        ]
    )

