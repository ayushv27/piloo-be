from .base import *


ENV_VARIABLE = 'prod'

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE'),
        'NAME': os.getenv('PROD_DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}




# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"
MEDIA_URL = 'media/'
STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR),'static')
MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), MEDIA_URL)

RTMP_HOST = os.getenv('RTMP_HOST')

CDN_DOMAIN = os.getenv('CDN_DOMAIN')
