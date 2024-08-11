from setuptools import setup, find_packages

def read_requirements():
    with open('requirements.txt') as req_file:
        return req_file.read().splitlines()

setup(
    name='stt_tools', 
    version='0.1.0',  
    description='Common openai and stt tools library',
    author='Jon Fox',
    author_email='jon@foxsolutions.dev',
    url='https://github.com/jon-fox/stt_tools',
    packages=find_packages(),
    install_requires=read_requirements(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)

# pip install -e .