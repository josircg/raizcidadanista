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

#Configurations for send email
REPLY_TO_EMAIL = 'raizmovimentocidanista@gmail.com'
DEFAULT_FROM_EMAIL = 'Raiz Cidadanista<raizmovimentocidanista@gmail.com>'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'raiz'
EMAIL_HOST_PASSWORD = 'raiz2016'
EMAIL_SUBJECT_PREFIX = u'Raiz Cidadanista - '
EMAIL_PORT = 25
EMAIL_USE_TLS = False

