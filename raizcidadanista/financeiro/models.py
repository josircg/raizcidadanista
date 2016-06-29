# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import Sum

from django.contrib.admin.models import LogEntry,  CHANGE
from django.contrib.contenttypes.models import ContentType
from utils.fields import BRDecimalField
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from django.db.models import signals
from django.dispatch import receiver
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from utils import url_display
from cms.email import sendmail

from cadastro.models import Membro



class PeriodoContabil(models.Model):
    class Meta:
        verbose_name = u'Período Contábil'
        verbose_name_plural = u'Períodos Contábeis'
        ordering = ['ciclo']

    ciclo = models.CharField(max_length=6)
    status = models.BooleanField(u'Aberto', default=True)

    def month(self):
        return self.ciclo[:4]

    def year(self):
        return self.ciclo[-2:]

    def __unicode__(self):
        return u'%s/%s' % (self.ciclo[:4], self.ciclo[-2:])


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


TIPO_OPER = (
    ('D', u'Depósito'),                     # Recurso do Concedente ou Convenente
    ('H', u'Cheque Devolvido'),             # Cheque não compensado pelo banco
    ('P', u'Pagamento'),                    # Pagamento de Contas a Fornecedores
    ('F', u'Rendimentos Financeiros'),      # Rendimentos Financeiros
    ('Q', u'Restituição'),                  # Restituição ao Concedente
    ('T', u'Transferência'),                # Transferência entre contas
    ('S', u'Saldo'),                        # Saldo informado pelo Banco/Operador
)
class Operacao(models.Model):
    class Meta:
        ordering = ['dt',]
        verbose_name = u'Operação'
        verbose_name_plural = u'Operações'

    conta = models.ForeignKey(Conta, verbose_name=u'Conta')
    tipo = models.CharField(u'Tipo', max_length=1, choices=TIPO_OPER)
    dt = models.DateField(u'Em')
    referencia = models.CharField(u'Referência', max_length=20)
    valor = models.DecimalField(u'Valor', max_digits=14, decimal_places=2)
    conferido = models.BooleanField(u'Conferido', default=False)
    obs = models.TextField(u'Obs', blank=True, null=True)

    def is_recebimento(self):
        return self.tipo in ('R','X','E')
    is_recebimento.boolean = True
    is_recebimento.short_description = u'Recebimento?'

    def is_pagamento(self):
        return self.tipo in ('P','Q','F')
    is_pagamento.boolean = True
    is_pagamento.short_description = u'Pagamento?'

    def is_deposito(self):
        return self.tipo == 'D'
    is_deposito.boolean = True
    is_deposito.short_description = u'Deposito?'

    def is_transferencia(self):
        return self.tipo == 'T'
    is_transferencia.boolean = True
    is_transferencia.short_description = u'Transferência?'

    def descricao_caixa(self):
        if self.is_pagamento():
            return url_display(self.pagamento)
        elif self.is_recebimento():
            return url_display(self.recebimento)
        elif self.is_transferencia():
            return url_display(self.transferencia)
        return u'<a href="%s">%s (%s)</a>' % (reverse('admin:convenio_operacao_change', args=(self.pk, )), self.get_tipo_display(), self.conta )
    descricao_caixa.short_description = u"Descrição"
    descricao_caixa.allow_tags = True

    def __unicode__(self):
        return u"%s - R$ %s" % (self.conta, self.valor, )

class Pagamento(Operacao):
    class Meta:
        verbose_name = u'Pagamento'
        verbose_name_plural = u'Pagamentos'

    colaborador = models.ForeignKey(Membro)

    def get_valor_positivo(self):
        return abs(self.valor or Decimal(0))

    def __unicode__(self):
        return u"R$ %s" % (self.valor, )
@receiver(signals.pre_save, sender=Pagamento)
def pagamento_update_valor_signal(sender, instance, *args, **kwargs):
    if instance.valor > 0:
        instance.valor = -instance.valor
@receiver(signals.pre_save, sender=Pagamento)
def pagamento_tipo_signal(sender, instance, *args, **kwargs):
    if not instance.tipo:
        instance.tipo = 'P'

class Transferencia(Operacao):
    class Meta:
        verbose_name = u'Transferência'
        verbose_name_plural = u'Transferências'

    destino = models.ForeignKey(Conta, verbose_name=u'Destino')
    transf_associada = models.ForeignKey('self', verbose_name=u'Trasf. associada', blank=True, null=True)

    def transf_associada_display(self):
        if self.transf_associada:
            return u'<a href="%s">%s</a>' % (reverse('admin:convenio_transferencia_change', args=(self.transf_associada.pk, )), self.transf_associada)
        return '-'
    transf_associada_display.short_description = u'Trasf. associada'
    transf_associada_display.allow_tags = True

    def save(self, *args, **kwargs):
        self.tipo = 'T'
        super(Transferencia, self).save(*args, **kwargs)
        if self.transf_associada:
            if (self.transf_associada.conta != self.destino) or (self.transf_associada.destino != self.conta) \
                    or (self.transf_associada.dt != self.dt) or (self.transf_associada.valor != -self.valor) \
                    or (self.transf_associada.conferido != self.conferido) or (self.transf_associada.referencia != self.referencia):
                self.transf_associada.conta = self.destino
                self.transf_associada.destino = self.conta
                self.transf_associada.dt = self.dt
                self.transf_associada.referencia = self.referencia
                self.transf_associada.valor = -self.valor
                self.transf_associada.conferido = self.conferido
                self.content_object.save()
        else:
            transf = Transferencia(
                conta=self.destino,
                destino=self.conta,
                dt=self.dt,
                referencia=self.referencia,
                valor=-self.valor,
                conferido=self.conferido,
                transf_associada=self
            )
            transf.save()
            self.transf_associada = transf
            self.save()

    def __unicode__(self):
        if self.valor > 0:
            return u'Transferência da conta %s' % self.destino
        else:
            return u'Transferência para conta %s' % self.destino


class ReceitaOperacao(Operacao):
    class Meta:
        verbose_name = u'Receita'
        verbose_name_plural = u'Receitas'

    colaborador = models.ForeignKey(Membro, blank=True, null=True)
    dtpgto = models.DateField(u'Dt. Conciliação', blank=True, null=True)

    def __unicode__(self):
        return u'%s/%s | R$ %s' % (self.conta, self.colaborador, self.valor)

    def save(self, *args, **kwargs):
        super(Receita, self).save(*args, **kwargs)
        if self.dtpgto and self.colaborador:
            if self.colaborador.contrib_prox_pgto is None or self.colaborador.contrib_prox_pgto < self.dt:
                if self.colaborador.contrib_tipo in ('1','3','6'):
                    self.colaborador.contrib_prox_pgto = self.dt + relativedelta(months=int(self.colaborador.contrib_tipo))
                    user = User.objects.get_or_create(username="sys")[0]
                    # Log do membro
                    LogEntry.objects.log_action(
                        user_id = user.pk,
                        content_type_id = ContentType.objects.get_for_model(self.colaborador).pk,
                        object_id = self.colaborador.pk,
                        object_repr = u"%s" % self.colaborador,
                        action_flag = CHANGE,
                        change_message = u'A data do Próximo Pagamento foi alterada para: %s' % self.colaborador.contrib_prox_pgto
                    )

                elif self.colaborador.contrib_tipo == 'A':
                    self.colaborador.contrib_prox_pgto = self.dt + relativedelta(year=self.dt.year+1)
                    user = User.objects.get_or_create(username="sys")[0]
                    # Log do membro
                    LogEntry.objects.log_action(
                        user_id = user.pk,
                        content_type_id = ContentType.objects.get_for_model(self.colaborador).pk,
                        object_id = self.colaborador.pk,
                        object_repr = u"%s" % self.colaborador,
                        action_flag = CHANGE,
                        change_message = u'A data do Próximo Pagamento foi alterada para: %s' % self.colaborador.contrib_prox_pgto
                    )
                else:
                    self.colaborador.contrib_prox_pgto = None
                self.colaborador.save()
@receiver(signals.post_save, sender=Receita)
def pagamentoidentificado_receita_signal(sender, instance, created, raw, using, *args, **kwargs):
    if instance.dtpgto and instance.colaborador and not instance.colaborador.status_email in ('S', 'O'):
        sendmail(
            subject=u'Raiz Movimento Cidadanista - Pagamento Identificado!',
            to=[instance.colaborador.email, ],
            bcc=list(User.objects.filter(groups__name=u'Financeiro').values_list('email', flat=True)),
            template='emails/pagamento-identificado.html',
            params={
                'receita': instance,
            },
        )


# Receita antiga
class Receita(models.Model):
    class Meta:
        ordering = ('conta__conta', )

    conta = models.ForeignKey(Conta)
    colaborador = models.ForeignKey(Membro, blank=True, null=True)
    dtaviso = models.DateField(u'Dt. Informada')
    valor = BRDecimalField(u'Valor Pago', max_digits=12, decimal_places=2)
    dtpgto = models.DateField(u'Dt. Conciliação', blank=True, null=True)
    nota = models.TextField(u'Nota', blank=True, null=True)


class MetaArrecadacao(models.Model):
    class Meta:
        verbose_name = u'Meta de Arrecadação'
        verbose_name_plural = u'Metas de Arrecadações'

    descricao = models.CharField(u'Descrição', max_length=100)
    data_inicial = models.DateField(u'Data inicial')
    data_limite = models.DateField(u'Data limite')
    valor = BRDecimalField(u'Valor', max_digits=12, decimal_places=2)

    def receitas(self):
        return Receita.objects.filter(dtpgto__gte=self.data_inicial).exclude(dtpgto__gt=self.data_limite)

    def acumulado(self):
        return self.receitas().aggregate(acumulado=Sum('valor')).get('acumulado', 0.0) or 0.0

    def falta(self):
        falta_valor = self.valor - self.acumulado()
        if falta_valor < 0:
            return 0.0
        return falta_valor

    def filiados_doaram(self):
        return (float(self.receitas().count())/(Membro.objects.count() or 1))*100

    def get_absolute_url(self):
        return reverse('meta', kwargs={'pk': self.pk, })

    def __unicode__(self):
        return self.descricao