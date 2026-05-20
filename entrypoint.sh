#!/bin/sh
set -e

case "$1" in
    gunicorn)
        echo "==> Running migrations..."
        python manage.py migrate --noinput
        echo "==> Collecting static files..."
        python manage.py collectstatic --noinput
        ;;
esac

exec "$@"
