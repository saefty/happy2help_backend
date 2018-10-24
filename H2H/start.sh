#!/bin/bash

# Start Gunicorn processes
echo Starting Gunicorn.
python3 ./manage.py makemigrations
python3 ./manage.py migrate

exec gunicorn H2H.wsgi \
    --bind 0.0.0.0:8000 \
    --workers 3