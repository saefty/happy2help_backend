#!/bin/bash

source ~/db_config_dev || true
docker login -u $DOCKER_USER -p $DOCKER_PW registry.taher.io || true

docker pull "registry.taher.io/h2h/django-backend/master:latest"
docker stop master && docker rm master
docker run --name master -e PRODUCTION=0 -e DB_NAME=$DB_NAME -e DB_USER=$DB_USER -e DB_PASSWORD=$DB_PASSWORD -e DB_HOST=$DB_HOST -e DB_PORT=$DB_PORT -d -p 8000:80 registry.taher.io/h2h/django-backend/master:latest