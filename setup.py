from setuptools import setup
from setuptools import find_packages


with open('requirements.txt', 'r') as f:
    requirements = f.read()


setup(
    name='most-client',
    version='1.0.41',
    python_requires=f'>=3.6',
    description='Most AI API for https://the-most.ai',
    url='https://github.com/the-most-ai/most-client',
    author='George Kasparyants',
    author_email='george@the-most.ai',
    license='',
    packages=find_packages(include=['most', 'most.*']),
    install_requires=requirements,
    zip_safe=True,
    include_package_data=True,
    exclude_package_data={'': ['notebooks']},
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6"
    ],
)
