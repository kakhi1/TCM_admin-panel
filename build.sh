#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
echo "Running migrations..."
python manage.py migrate --noinput
python manage.py collectstatic --no-input --clear

# Try to create superuser. If it exists, skip without error.
python manage.py createsuperuser --noinput || true