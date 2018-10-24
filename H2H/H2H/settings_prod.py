
# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASES = {
   'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME':  os.getenv('DB_NAME', None),
        'USER':  os.getenv('DB_USER', None),
        'PASSWORD': os.getenv('DB_PASSWORD', None),
        'HOST':  os.getenv('DB_HOST', None),
        'PORT':  os.getenv('DB_PORT', None),
    },
}