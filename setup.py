from setuptools import setup, find_packages


with open('README') as f:
    long_description = ''.join(f.readlines())


setup(
    name='labelord',
    version='0.3',
    description='Synchronizes label in configurre GitHub repositories.',
    long_description=long_description,
    author='Michal Klement',
    author_email='klememi1@fit.cvut.cz',
    license='MIT License',
    url='https://github.com/klememi/labelord_klememi1',
    packages=find_packages(),
    package_data={'labelord': ['templates/*.html', 'static/bg.jpg']},
    python_requires='~=3.6',
    install_requires=['click>=6.7', 'Flask>=0.12.2', 'requests>=2.18.4'],
    entry_points={
        'console_scripts': [
            'labelord = labelord.cli:main',
        ],
    },
    keywords='github,label,cvut,fit',
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'License :: OSI Approved :: MIT License',
        'Environment :: Console',
        'Framework :: Flask',
        'Topic :: Utilities',
        'Topic :: Education',
        'Topic :: Software Development :: Version Control :: Git',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        ],
    zip_safe=False,
)