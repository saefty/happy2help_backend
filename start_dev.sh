#!/bin/bash

exec docker run --name develop -v ./H2H/db.sqlite3:./db.sqlite3 -e PRODUCTION=false -d -p 8000:80 registry.taher.io/h2h/django-backend/develop
