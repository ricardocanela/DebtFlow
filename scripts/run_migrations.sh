#!/bin/bash
# Run Django migrations
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating pg_trgm extension if needed..."
python -c "
import django
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm;')
    print('pg_trgm extension ready')
"

echo "Migrations complete!"
