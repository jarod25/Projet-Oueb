#!/bin/sh
python3 manage.py collectstatic --noinput --clear
python3 manage.py migrate
python3 manage.py runserver --noreload 0.0.0.0:8000
