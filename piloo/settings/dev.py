from .base import *


ENV_VARIABLE = 'dev'

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE'),
        'NAME': os.getenv('DEV_DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

RTMP_HOST = os.getenv('RTMP_HOST')

CDN_DOMAIN = os.getenv('CDN_DOMAIN')

STATIC_URL = f'{CDN_DOMAIN}/static/'
MEDIA_URL = f'https://{CDN_DOMAIN}/'
STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR),'static')
MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'media')


