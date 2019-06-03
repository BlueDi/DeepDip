from setuptools import setup

setup(
    name='gym_diplomacy',
    version='0.0.2',
    install_requires=[
        'grpcio',
        'grpcio-tools',
        'gym>=0.11.0',
        'numpy',
        'protobuf>=3.7.0'
    ]
)
