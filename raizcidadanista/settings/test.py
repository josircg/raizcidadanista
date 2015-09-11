# -*- coding: utf-8 -*-
from settings import *

DEBUG = False
TEMPLATE_DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'raiz',
        'USER': 'raiz',
        'PASSWORD': 'logica38',
        'HOST': '',
        'PORT': '',
    },
}

ALLOWED_HOSTS = ['site4.irdx.com.br', 'teste.raiz.org.br', ]

SITE_HOST = 'http://teste.raiz.org.br'

