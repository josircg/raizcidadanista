# coding:utf-8
from datetime import datetime, timedelta, date

from django.db import models
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db.models import signals
from django.dispatch import receiver

#from smart_selects.db_fields import ChainedForeignKey
#from utils.models import BRDateField, BRDecimalField
#from utils.fields import formata_nome_do_arquivo, nome_arquivo_aberto
#from utils.email import sendmail

class UF(models.Model):

    REGIAO_UF = (
        ('N',  u'Norte'),
        ('NE', u'Nordeste'),
        ('S',  u'Sul'),
        ('SE', u'Sudeste'),
        ('CO', u'Centro Oeste'),
        )

    codigo = models.CharField(max_length=2, primary_key=True)
    nome = models.CharField(max_length=30)
    regiao = models.CharField(max_length=2, choices=REGIAO_UF)

    def __unicode__(self):
        return u'%s' % self.nome

GENDER = (
        ('M', u'Masculino'),
        ('F', u'Feminino'),
        ('O', u'Outros'),
        )

class Membro(models.Model):
    nome = models.CharField(u'Nome Completo',max_length=150)
    email = models.EmailField(u'Email', blank=True)
    sexo = models.CharField(max_length=1, choices=GENDER, default='O')
#    dtnascimento = models.DateField(u'Dt.Nascimento', blank=True, null=True)
#    atividade_profissional=models.CharField(u'Atividade Profissional',max_length=150, blank=True, null=True)
#    rg =models.CharField(u'RG',max_length=50, blank=True, null=True)
#    titulo_eleitoral=models.CharField(u'Título Eleitoral',max_length=50, blank=True, null=True)
#    municipio = models.CharField(u'Município',max_length=150, blank=True, null=True)
#    uf = models.ForeignKey(UF, blank=True, null=True)
#    municipio_eleitoral= models.CharField(u'Município Eleitoral',max_length=100, blank=True, null=True)
#   uf_eleitoral = models.ForeignKey(u'UF do Domicílio Eleitoral',UF, blank=True, null=True)
#    filiacao_partidaria = models.CharField(u'Filiação Partidária',max_length=100)
#    usuario = models.ForeignKey(User, verbose_name=u'Usuário', blank=True, null=True)
#    facebook_id = models.CharField(u'Facebook ID', max_length=120, editable=False, blank=True, null=True)
#    facebook_access_token = models.TextField(editable=False, blank=True, null=True)
#    aprovador = models.ForeignKey(User, verbose_name=u'Aprovador')

    class Meta:
        ordering = ['nome',]

    def __unicode__(self):
        return u'%s (%s)' % (self.nome, self.email)


CIRCULO_TIPO = (
    ('R', u'Regional'),
    ('T', u'Temático'),
)


class Circulo(models.Model):
    class Meta:
        verbose_name = u'Círculo'

    titulo = models.CharField(u'Título', max_length=80)
    descricao = models.TextField(u'Descricao') # HTML
    tipo = models.CharField(u'Tipo', max_length=1, choices=CIRCULO_TIPO)
    uf = models.ForeignKey(UF, blank=True, null=True)
    municipio = models.CharField(u'Município',max_length=150, blank=True, null=True)
    oficial = models.BooleanField(u'Grupo Oficial', default=False)
    dtcadastro = models.DateField(u'Dt.Cadastro')
    site_externo = models.URLField(u'Site/Blog/Fanpage', blank=True, null=True)

    def __unicode__(self):
        return u'Círculo %s %s' % (self.get_tipo_display(), self.titulo)

class CirculoMembro(models.Model):
    circulo = models.ForeignKey(Circulo)
    membro = models.ForeignKey(Membro)
    administrador = models.BooleanField()
#    tipo_alerta = models.CharField(u'Recebimento de Notificações') # Frequência de recebimento de alertas
#    representante = models.ForeignKey(Membro) # Membro que representa alguém no Círculo

# Eventos que devem ser divulgados no site

class CirculoEvento(models.Model):
    circulo = models.ForeignKey(Circulo)
    nome = models.CharField(u'Título', max_length=100)
    dt_evento = models.DateTimeField(u'Dt.Evento')
    local = models.TextField(u'Local do Evento')

# Fóruns - Baseado no modelo de dados do Loomio

'''
STATUS_DISCUSSAO = (
    ('A', u'Aberto'),
    ('F', u'Fechado'),
    ('V', u'Votação Iniciada'),
    ('X', u'Votação Finalizada'),
    )

class Topico(models.Model):
    criador = models.ForeignKey(Membro)
    titulo = models.CharField(u'Título', max_length=200)
    status = models.CharField(u'Status', max_length=1, choices=STATUS_DISCUSSAO)
    dt_ultima_atualizacao = models.DateTimeField(u"Ultima atualização", blank=True, null=True)
    visitacoes = models.IntegerField(default=0)

class Conversa(models.Model):
    discussao = models.ForeignKey(Topico)
    autor = models.ForeignKey(Membro)
    texto = models.TextField()
    dt_criacao = models.DateTimeField(u'Data de criação', auto_now_add=True)
    proposta = models.BooleanField(u'Proposta')

class Votacao(models.Model):
    discussao = models.ForeignKey(Conversa)
    eleitor = models.ForeignKey(Membro)
    voto = models.CharField(u'Tipo de Votação',max_length=1)
'''
