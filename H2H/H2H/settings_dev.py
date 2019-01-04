
# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASES = {
   'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':  'happy2help',
        'USER': os.environ.get('DB_USER', None),
        'PASSWORD': os.environ.get('DB_PW', None),
        'HOST':  '127.0.0.1',
        'PORT':  1337,
    },
}