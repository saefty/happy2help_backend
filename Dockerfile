FROM python:3
RUN mkdir /django
WORKDIR /django

RUN apt-get update --yes && apt-get upgrade --yes
RUN apt-get install nginx supervisor --yes

ADD . /django/
RUN pip install -r requirements.txt
COPY ./supervisord.conf /etc/supervisor/supervisord.conf
COPY ./nginx_conf /etc/nginx/sites-available/app
RUN ln -s /etc/nginx/sites-available/app /etc/nginx/sites-enabled
WORKDIR /django/H2H
RUN python manage.py migrate
RUN python manage.py collectstatic

EXPOSE 80
ENV PRODUCTION true
ENV PYTHONUNBUFFERED 1

RUN chmod +x ./start.sh
CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
