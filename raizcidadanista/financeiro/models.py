# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import Sum

from django.contrib.admin.models import LogEntry,  CHANGE
from django.contrib.contenttypes.models import ContentType
from utils.fields import BRDecimalField
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.contrib.contenttypes import generic
from django.db.models import signals
from django.dispatch import receiver
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from utils import url_display
from utils.stdlib import nvl
from cms.email import sendmail

from cadastro.models import Membro

from decimal import Decimal


class PeriodoContabil(models.Model):
    class Meta:
        verbose_name = u'Período Contábil'
        verbose_name_plural = u'Períodos Contábeis'
        ordering = ['ciclo']

    ciclo = models.CharField(max_length=6, help_text='Entre no formato AAAAMM onde AAAA é o Ano e MM o mês')
    status = models.BooleanField(u'Aberto', default=True)
    publico = models.BooleanField(u'Público', default=False)

    def month(self):
        return self.ciclo[:4]

    def year(self):
        return self.ciclo[-2:]

    def __unicode__(self):
        return u'%s/%s' % (self.ciclo[:4], self.ciclo[-2:])


CONTA_TIPO_CHOICES = (
    ('B', u'Conta Banco'),
    ('M', u'Movimento'),
    ('P', u'Provisão'),
)

class Conta(models.Model):
    class Meta:
        ordering = ('conta', )

    conta = models.CharField(u'Conta', max_length=10, unique=True)
    conta_contabil = models.CharField(u'Conta Contábil', max_length=15)
    descricao = models.CharField(u'Descrição', max_length=60)
    tipo = models.CharField(u'Tipo', max_length=1, choices=CONTA_TIPO_CHOICES, default='M')
    ativa = models.BooleanField(default=True)
    nota = models.TextField(u'Nota Explicativa', blank=True, null=True )

    def __unicode__(self):
        return u'%s' % self.conta

class TipoDespesa(models.Model):
    class Meta:
        verbose_name = u'Tipo de Despesa'
        verbose_name_plural = u'Tipos de Despesa'

    codigo = models.CharField(u'Código Externo', max_length=20)
    descricao_breve = models.CharField(u'Conta Contábil', max_length=20)
    descricao = models.CharField(u'Descrição', max_length=80)

    def __unicode__(self):
        return u'%s' % (self.descricao )

class Projeto(models.Model):
    nome = models.CharField(u'Nome', max_length=40)
    descricao = models.TextField(u'Descrição')
    orcamento = BRDecimalField(u'Valor', max_digits=16, decimal_places=2)
    dtinicio = models.DateField(u'Dt.Início')
    dtfim = models.DateField(u'Dt.Final')
    responsavel = models.ForeignKey(User)
    ativo = models.BooleanField(u'Permite lançamentos',default=True)

    def __unicode__(self):
        return u'%s' % self.nome

class Fornecedor(models.Model):
    class Meta:
        ordering = ('nome', )
        verbose_name_plural = u'Fornecedores'

    nome = models.CharField(u'Fornecedor', max_length=80)
    identificador = models.CharField('CPF/CNPJ', max_length=14)
    dados_financeiros = models.TextField(u'Dados financeiros', blank=True, null=True)
    servico_padrao = models.ForeignKey(TipoDespesa, verbose_name=u'Tipo de Despesa Padrão', blank=True, null=True)
    ativo = models.BooleanField(u'Ativo')

    def tipo(self):
        return 'PF' if len(self.identificador) == 11 else 'PJ'

    def get_identificador_display(self):
        identificador = self.identificador
        if self.tipo() == 'PF':
            identificador = u'%s.%s.%s-%s' % (identificador[0:3], identificador[3:6], identificador[6:9], identificador[9:11])
        else:
            identificador = u'%s.%s.%s/%s-%s' % (identificador[0:2], identificador[2:5], identificador[5:8], identificador[8:12], identificador[12:14])
        return identificador

    def __unicode__(self):
        return u"%s" % self.nome


class Despesa(models.Model):
    fornecedor = models.ForeignKey(Fornecedor, verbose_name=u'Fornecedor')
    tipo_despesa = models.ForeignKey(TipoDespesa, verbose_name=u'Tipo de Despesa', blank=True, null=True)
    dtemissao = models.DateField(u'Data de Emissão')
    dtvencimento = models.DateField(u'Data de Vencimento', blank=True, null=True)
    documento = models.CharField('Referência', max_length=30, blank=True, null=True)
    valor = BRDecimalField(u'Valor', max_digits=14, decimal_places=2)
    integral = models.BooleanField(u'Pagamento integral', default=False)
    observacoes = models.TextField(u'Observações', blank=True, null=True)

    def clean(self):
        if self.integral and not Conta.objects.filter(tipo='B').exists():
            raise ValidationError(u'O sistema ainda não possui nenhuma Conta Banco associada. Crie uma Conta Banco, antes de marcar a Despesa como "Pagamento integral".')

    def saldo_a_pagar(self):
        return (self.valor or Decimal(0)) + (self.pagamento_set.aggregate(pago=Sum('valor')).get('pago') or Decimal(0))

    def __unicode__(self):
        return u"%s - %s" % (self.fornecedor, self.dtemissao.strftime('%d/%m/%Y'), )

@receiver(signals.post_save, sender=Despesa)
def despesa_update_convenio_signal(sender, instance, created, *args, **kwargs):
    instance.pagamento_set.update(fornecedor=instance.fornecedor, tipo='P')

@receiver(signals.post_save, sender=Despesa)
def despesa_update_pagamento_integral_signal(sender, instance, created, *args, **kwargs):
    if instance.integral:
        if not instance.pagamento_set.exists():
            conta = Conta.objects.filter(tipo='B').latest('pk')
            Pagamento(
                conta=conta,
                tipo='P',
                dt=instance.dtvencimento or datetime.today(),
                referencia=instance.documento,
                valor=instance.valor,
                fornecedor=instance.fornecedor,
                despesa=instance,
            ).save()
        else:
            pagamento = instance.pagamento_set.latest('pk')
            pagamento.dt = instance.dtvencimento or datetime.today()
            pagamento.referencia = instance.documento
            pagamento.valor = instance.valor
            pagamento.save()


# Intenção ou Aviso de Receita
class Receita(models.Model):
    class Meta:
        ordering = ('conta__conta', )

    conta = models.ForeignKey(Conta)
    colaborador = models.ForeignKey(Membro, blank=True, null=True)
    dtaviso = models.DateField(u'Dt. Informada')
    valor = BRDecimalField(u'Valor Pago', max_digits=12, decimal_places=2)
    dtpgto = models.DateField(u'Dt. Depósito', blank=True, null=True)
    notificado = models.BooleanField(default=False)
    nota = models.TextField(u'Nota', blank=True, null=True)

    def __unicode__(self):
        return u'%s/%s | R$ %s' % (self.conta, self.colaborador, self.valor)

    def save(self, *args, **kwargs):

        super(Receita, self).save(*args, **kwargs)
        if self.dtpgto:
            #Se houver dtpgto, gravar o depósito na conta indicada
            if not Deposito.objects.filter(receita=self):
                Deposito(
                    receita=self,
                    conta=self.conta,
                    tipo='D',
                    dt=self.dtpgto,
                    referencia='',
                    valor=self.valor,
                ).save()
            else:
                Deposito.objects.filter(receita=self).update(
                    conta=self.conta,
                    dt=self.dtpgto,
                    referencia='',
                    valor=self.valor,
                )

            if nvl(self.notificado,False) == False:
                if self.colaborador and not self.colaborador.status_email in ('S', 'O'):
                    sendmail(
                        subject=u'Pagamento Identificado!',
                        to=[self.colaborador.email, ],
                        bcc=list(User.objects.filter(groups__name=u'Financeiro').values_list('email', flat=True)),
                        template='emails/pagamento-identificado.html',
                        params={'receita': self,},
                    )
                    self.notificado = True
                    super(Receita, self).save(*args, **kwargs)

        if self.colaborador and self.dtpgto:
            prox_data = None
            if self.colaborador.contrib_prox_pgto == None:
                prox_data = self.dtpgto
            else:
                if self.colaborador.contrib_prox_pgto > self.dtpgto:
                    prox_data = None
                else:
                    prox_data = self.colaborador.contrib_prox_pgto

            if prox_data:
                if self.colaborador.contrib_tipo in ('1','3','6'):
                    prox_data = prox_data + relativedelta(months=int(self.colaborador.contrib_tipo))
                else:
                    prox_data = prox_data + relativedelta(year=self.dtpgto.year+1)

                self.colaborador.contrib_prox_pgto = prox_data
                self.colaborador.save()
                # Log do membro
                user = User.objects.get_or_create(username="sys")[0]
                LogEntry.objects.log_action(
                            user_id = user.pk,
                            content_type_id = ContentType.objects.get_for_model(self.colaborador).pk,
                            object_id = self.colaborador.pk,
                            object_repr = u"%s" % self.colaborador,
                            action_flag = CHANGE,
                            change_message = u'A data do Próximo Pagamento foi alterada para: %s' %prox_data
                )

TIPO_OPER = (
    ('D', u'Deposito à vista'),             # Receita de colaborador ou filiado
    ('C', u'Depósito a compensar'),         # Depósito em cheque/a compensar
    ('H', u'Cheque Devolvido'),             # Cheque não compensado pelo banco
    ('P', u'Pagamento'),                    # Pagamento de Contas a Fornecedores
    ('F', u'Rendimentos Financeiros'),      # Rendimentos Financeiros
    ('Q', u'Restituição'),                  # Restituição a fornecedores ou colaboradores
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

    def is_deposito(self):
        return self.tipo == 'D'
    is_deposito.boolean = True
    is_deposito.short_description = u'Deposito?'

    def is_pagamento(self):
        return self.tipo in ('P', 'Q', )
    is_pagamento.boolean = True
    is_pagamento.short_description = u'Pagamento?'

    def is_transferencia(self):
        return self.tipo == 'T'
    is_transferencia.boolean = True
    is_transferencia.short_description = u'Transferência?'

    def descricao_caixa(self):
        if self.is_pagamento():
            return url_display(self.pagamento)
        elif self.is_deposito():
            return url_display(self.deposito)
        elif self.is_transferencia():
            return url_display(self.transferencia)
        return u'<a href="%s">%s (%s)</a>' % (reverse('admin:convenio_operacao_change', args=(self.pk, )), self.get_tipo_display(), self.conta )
    descricao_caixa.short_description = u"Descrição"
    descricao_caixa.allow_tags = True

    def __unicode__(self):
        return u"%s - R$ %s" % (self.descricao_caixa, self.valor, )


class Pagamento(Operacao):
    class Meta:
        verbose_name = u'Pagamento'
        verbose_name_plural = u'Pagamentos'

    fornecedor = models.ForeignKey(Fornecedor)
    projeto = models.ForeignKey(Projeto, blank=True, null=True)
    tipo_despesa = models.ForeignKey(TipoDespesa, verbose_name=u'Tipo de Despesa', blank=True, null=True)
    despesa = models.ForeignKey(Despesa, blank=True, null=True)

    def get_valor_positivo(self):
        return abs(self.valor or Decimal(0))

    def __unicode__(self):
        return u"%s (%s)" % (self.tipo_despesa, self.fornecedor, )

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
                self.transf_associada.save()
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


class Deposito(Operacao):
    class Meta:
        verbose_name = u'Depósito'

    receita = models.ForeignKey(Receita, blank=True, null=True)

    def __unicode__(self):
        if self.receita:
            return u'Depósito %s | R$ %s' % (self.receita.colaborador, self.valor)
        else:
            return u'Depósito | R$ %s' % self.valor


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
