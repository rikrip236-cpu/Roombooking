#!/bin/sh
set -e
echo "Attente de PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do sleep 0.5; done
echo "PostgreSQL disponible"
python manage.py makemigrations accounts rooms bookings --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec "$@"
