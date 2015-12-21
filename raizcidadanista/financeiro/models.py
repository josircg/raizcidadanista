# -*- coding: utf-8 -*-
from django.db import models

from utils.fields import BRDecimalField
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from django.db.models import signals
from django.dispatch import receiver
from django.contrib.auth.models import User

from cms.email import sendmail

from cadastro.models import Membro


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

    def save(self, *args, **kwargs):
        super(Receita, self).save(*args, **kwargs)
        if self.dtpgto:
            if self.colaborador.contrib_prox_pgto is None or self.colaborador.contrib_prox_pgto < self.dtaviso:
                if self.colaborador.contrib_tipo in ('1','3','6'):
                    self.colaborador.contrib_prox_pgto = self.dtaviso + relativedelta(months=int(self.colaborador.contrib_tipo))
                elif self.colaborador.contrib_tipo == 'A':
                    self.colaborador.contrib_prox_pgto = self.dtaviso + relativedelta(year=1)
                else:
                    self.colaborador.contrib_prox_pgto = None
                self.colaborador.save()
@receiver(signals.post_save, sender=Receita)
def pagamentoidentificado_receita_signal(sender, instance, created, raw, using, *args, **kwargs):
    if instance.dtpgto:
        sendmail(
            subject=u'Raiz Movimento Cidadanista - Pagamento Identificado!',
            to=[instance.colaborador.email, ],
            bcc=list(User.objects.filter(groups__name=u'Financeiro').values_list('email', flat=True)),
            template='emails/pagamento-identificado.html',
            params={
                'receita': instance,
            },
        )