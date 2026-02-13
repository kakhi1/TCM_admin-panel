# #!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
echo "Running migrations..."
python manage.py migrate --noinput
python manage.py collectstatic --no-input --clear

# Try to create superuser. If it exists, skip without error.
python manage.py createsuperuser --noinput || true
#!/usr/bin/env bash
# set -o errexit

# echo "Installing dependencies..."
# pip install -r requirements.txt

# echo "Running migrations..."
# python manage.py migrate --noinput

# echo "Collecting static files..."
# python manage.py collectstatic --noinput --clear

# echo "Creating superuser if needed..."
# # Only try to create superuser if username is provided
# if [ -n "$DJANGO_SUPERUSER_USER" ]; then
#     python manage.py createsuperuser \
#         --noinput \
#         --username $DJANGO_SUPERUSER_USER \
#         --email $DJANGO_SUPERUSER_EMAIL || true
# else
#     echo "Skipping superuser creation - DJANGO_SUPERUSER_USER not set"
# fi

# echo "Build completed successfully!"