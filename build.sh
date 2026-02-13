#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Try to create superuser. If it exists, skip without error.
python manage.py createsuperuser --noinput || true