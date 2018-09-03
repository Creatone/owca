from setuptools import setup, find_packages

setup(
    name='wrapper',
    version='0.0.1',
    author='Intel',
    description='Workloads wrapper for running and exposing application performance metrics ',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Distributed Computing',
    ],
    install_requires=[
        # owca package version should comply with current version in the owca submodule
        'owca==0.1.dev71+gfc07b90',
    ],
    tests_require=[
        'pytest',
        'pytest-cov',
        'flake8'
    ],
    packages=find_packages(),
    python_requires=">=3.6",
)
