# -*- coding: utf-8 -*-
from django.db import models

from cadastro.models import Membro
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

    def __unicode__(self):
        return u'%s' % self.conta


class Receita(models.Model):
    class Meta:
        ordering = ('conta__conta', )

    conta = models.ForeignKey(Conta)
    colaborador = models.ForeignKey(Membro)
    dtaviso = models.DateField(u'Dt. Informada')
    valor  = BRDecimalField(u'Valor Pago', max_digits=12, decimal_places=2)
    dtpgto = models.DateField(u'Dt. Conciliação', blank=True, null=True)

    def __unicode__(self):
        return u'%s/%s | R$ %s' % (self.conta, self.colaborador, self.valor)