# coding:utf-8
from datetime import datetime, timedelta, date

from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.db import models
from django.conf import settings
from django.db.models import signals, F
from django.dispatch import receiver

from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Template
from django.template.context import Context
from threading import Thread

from cdastro.models import Membro
from forum.models import Grupo, GrupoUsuario
from utils.fields import BRDecimalField

CONTA_TIPO_CHOICES = (
    ('M', u'Movimento'),
    ('P', u'Provisão'),
)

class Conta(models.Model):
    class Meta:
        ordering = ('conta', )

    conta = models.CharField(u'Conta', max_length=10, unique=True)
    descricao = models.CharField(u'Descrição', max_length=60)
    tipo = models.CharField(u'Tipo', max_length=1, choices=CONTA_TIPO_CHOICES, default='M')
    ativa = models.BooleanField(default=True)
    nota = models.TextField(u'Nota Explicativa', blank=True, null=True )

class Receita(models.Model):

    class Meta:
        ordering = ['conta__nome',]

    conta = models.ForeignKey(Conta)
    colaborador = models.ForeignKey(Membro)
    dtaviso = models.DateField('Dt.Informada')
    valor  = BRDecimalField('Valor Pago')
    dtpgto = models.DateField('Dt.Conciliacao', blank=True, null=True)


