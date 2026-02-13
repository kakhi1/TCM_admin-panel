# #!/usr/bin/env bash
# set -o errexit

# pip install -r requirements.txt
# python manage.py collectstatic --no-input
# python manage.py migrate

# # Try to create superuser. If it exists, skip without error.
# python manage.py createsuperuser --noinput || true
#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Install Dependencies
pip install -r requirements.txt

# 2. Collect Static Files (CRITICAL FIX: --noinput, not --no-input)
# Added --clear to wipe old files so you get a fresh start
python manage.py collectstatic --noinput --clear

# 3. Migrate Database
python manage.py migrate

# 4. Create Superuser (Optional - requires env vars to work)
# This will only work if you have set DJANGO_SUPERUSER_USERNAME etc. in Seenode variables.
# The '|| true' ensures the build doesn't fail if the user already exists.
python manage.py createsuperuser --noinput || true