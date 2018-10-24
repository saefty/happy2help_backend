#!/bin/bash

docker pull "registry.taher.io/h2h/django-backend/develop:latest"
docker stop develop && docker rm develop
docker run --name develop -v "$PWD/H2H/db.sqlite3":"/django/H2H/db.sqlite3" -e PRODUCTION=0 -d -p 8000:80 registry.taher.io/h2h/django-backend/develop:latest