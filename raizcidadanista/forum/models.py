# -*- coding: utf-8 -*-
from django.db import models
from utils.storage import UuidFileSystemStorage

from cadastro.models import Circulo, Membro

STATUS_TOPICO = (
    ('A', u'Aberto'),
    ('F', u'Fechado'),
)

STATUS_NOTIFICACAO = (
    ('N', u'Nenhum'),
    ('R', u'Resumo Diário'),
    ('I', u'Intenso'),
    ('V', u'Somente votações'),
)

TIPO_VOTO =  (
    ('A', u'De acordo'),
    ('S', u'Abstém'),
    ('D', u'Em desacordo'),
    ('B', u'Bloqueia'),
)

STATUS_CURTIDA = (
    ('C', u'Curtiu'),
    ('N', u'Não curtiu'),
)

STATUS_PROPOSTA = (
    ('A', u'Aberto'),
    ('F', u'Fechado'),
)

class Topico(models.Model):
    class Meta:
        verbose_name = u'Tópico'
        verbose_name_plural = u'Tópicos'

    titulo = models.CharField(u'Título', max_length=200)
    grupo = models.ForeignKey(Circulo)
    status = models.CharField(u'Status', max_length=1, choices=STATUS_TOPICO)
    criador = models.ForeignKey(Membro)
    dt_criacao = models.DateTimeField(u"Criação", auto_now_add=True)
    dt_ultima_atualizacao = models.DateTimeField(u"Ultima atualização", blank=True, null=True)
    visitacoes = models.IntegerField(default=0)

    def __unicode__(self):
        return u'%s' % self.titulo


class TopicoOuvinte(models.Model):
    class Meta:
        verbose_name = u'Participante'
        verbose_name_plural = u'Participantes'

    topico = models.ForeignKey(Topico)
    ouvinte = models.ForeignKey(Membro)
    notificacao = models.CharField(u'Tipo de Notificação', max_length=1, choices=STATUS_NOTIFICACAO)
    dtentrada = models.DateTimeField(u'Data de criação', auto_now_add=True)

    def __unicode__(self):
        return u'%s/%s' % (self.topico, self.colaborador)


class Conversa(models.Model):
    topico = models.ForeignKey(Topico)
    autor = models.ForeignKey(Membro)
    texto = models.TextField()
    dt_criacao = models.DateTimeField(u'Data de criação', auto_now_add=True)
    arquivo = models.FileField('Arquivo opcional com descrição ', upload_to='forum', blank=True, null=True, storage=UuidFileSystemStorage())
    conversa_pai = models.ForeignKey('self', blank=True, null=True)

    def __unicode__(self):
        return u'%s/%s' % (self.topico, self.autor)


class ConversaCurtida(models.Model):
    conversa = models.ForeignKey(Conversa)
    colaborador = models.ForeignKey(Membro)
    curtida = models.CharField(u'Curtiu?', max_length=1, choices=STATUS_CURTIDA)

    def __unicode__(self):
        return u'#%s - %s' % (self.pk, self.get_curtida_display(), )


# Conversa sujeita a votação
class Proposta(Conversa):
    dt_encerramento = models.DateTimeField(u'Data de encerramento')
    status = models.CharField(u'Situação', max_length=1, choices=STATUS_PROPOSTA)

    def __unicode__(self):
        return u'#%s - %s' % (self.pk, self.get_status_display(), )


# Voto na proposta
class Voto(models.Model):
    proposta = models.ForeignKey(Proposta)
    eleitor = models.ForeignKey(Membro)
    voto = models.CharField(u'Tipo de Votação', max_length=1, choices=TIPO_VOTO)

    def __unicode__(self):
        return u'#%s - %s' % (self.pk, self.get_voto_display(), )