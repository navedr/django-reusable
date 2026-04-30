#!/bin/bash
set -e

PYTHON="$HOME/.virtualenvs/django-reusable/bin/python"
TWINE="$HOME/.virtualenvs/django-reusable/bin/twine"

cd "$(dirname "$0")"

# clean
rm -rf dist/* build/*

# build + increment version
$PYTHON setup.py sdist bdist_wheel increment_version

# upload
$TWINE upload dist/*
