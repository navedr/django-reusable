import setuptools

setuptools.setup(
    name='django-reusable',
    version='0.1',
    author='Naved Rangwala',
    author_email='naved@ecarone.com',
    description='Agnostic and easy to use reusable library for django',
    url='http://dajaxproject.com',
    license='BSD',
    packages=['django_reusable',
              'django_reusable.templatetags'],
    package_data={'django_reusable': ['templates/django_reusable/*']},
    long_description=("Easy to use AJAX library for django, all the "
                      "presentation logic resides outside the views and "
                      "doesn't require any JS Framework. Dajaxice uses the "
                      "unobtrusive standard-compliant (W3C) XMLHttpRequest "
                      "1.0 object."),
    install_requires=[
        'Django>=2.2'
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
