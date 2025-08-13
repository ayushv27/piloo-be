from .base import *

ROOT_URLCONF = 'piloo.urls'
ENV_VARIABLE = 'test'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        # 'NAME': 'piloo_db_test',
        # 'USER': 'piloo_test',
        # 'PASSWORD': 'piloo123',
        'USER': 'piloo',
        'PASSWORD': 'oolip',
        'NAME': 'piloo_db',       
        # 'HOST':'10.16.140.21',        
        # 'HOST': 'host.docker.internal',  # or 'db' if using Docker
        'HOST': 'db',
        'PORT': '5432',
        'TEST': {
            'NAME': 'test_db',
        },
    }
}


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),    
}


class DisableMigrations(object):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

RECEIPENT_LIST = ['admin@test.com']

REDIS_HOST = "redis"
REDIS_PORT = 6379

RTMP_HOST = "localhost" 
CDN_DOMAIN = "localhost"