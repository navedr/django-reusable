import setuptools

version = float(open('version.txt', 'r').read())
version = round(version + 0.1, 1)
open('version.txt', 'w').write(str(version))

setuptools.setup(
    name='django-reusable',
    version=str(version),
    author='Naved Rangwala',
    author_email='naved@ecarone.com',
    description='Agnostic and easy to use reusable library for django',
    url='https://github.com/navedr/django-reusable',
    license='BSD',
    packages=['django_reusable',
              'django_reusable.templatetags'],
    package_data={'django_reusable': ['templates/django_reusable/*']},
    long_description="django-reusable is a collection of common functionality needed in most Django projects.",
    install_requires=[
        'Django>=2.0'
    ],
    classifiers=['Development Status :: 4 - Beta',
                 'Environment :: Web Environment',
                 'Framework :: Django',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: BSD License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Topic :: Utilities']
)
