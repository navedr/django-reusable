from pathlib import Path

import setuptools
import sys

version = float(open('version.txt', 'r').read())
if 'increment_version' in sys.argv:
    version = round(version + 0.1, 1)
    print('incrementing version to', version)
    open('version.txt', 'w').write(str(version))
    sys.argv.remove('increment_version')

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setuptools.setup(
    name='django-reusable',
    version=str(version),
    author='Naved Rangwala',
    author_email='naved@ecarone.com',
    description='Agnostic and easy to use reusable library for django',
    url='https://github.com/navedr/django-reusable',
    license='BSD',
    packages=['django_reusable',
              'django_reusable.migrations',
              'django_reusable.templatetags',
              'django_reusable.django_tables2'],
    include_package_data=True,
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'Django>=2.0',
        'django-tables2>=1.21.2',
        'django-crispy-forms>=1.7.2',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities'
    ]
)
