# -*- coding: utf-8 -*-
from django.db import models
from utils.storage import UuidFileSystemStorage
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.db.models import signals
from django.dispatch import receiver
from django.conf import settings

from smart_selects.db_fields import ChainedForeignKey
from cadastro.telegram import bot
from cms.email import sendmail

from datetime import datetime, timedelta


LOCALIZACAO = (
    ('N', u'Nacional'),
    ('E', u'Estadual'),
    ('M', u'Municipal'),
)
class Grupo(models.Model):
    class Meta:
        verbose_name = "Grupo"
        verbose_name_plural = "Grupos"

    nome = models.CharField(u'Nome', max_length=60)
    localizacao = models.CharField(u'Localização', max_length=1, choices=LOCALIZACAO)
    tematico = models.BooleanField(u'Temático', default=False)
    descricao = models.TextField(u'Descricao')

    def get_absolute_url(self):
        return reverse('forum_grupo', kwargs={'pk': self.pk, })

    def dt_ultima_atualizacao(self):
        try:
            return self.topico_set.latest('dt_ultima_atualizacao').dt_ultima_atualizacao
        except Topico.DoesNotExist:
            return None

    def num_topicos_nao_lidos(self, usuario):
        num = 0
        for topico in self.topico_set.filter(status='A'):
            if topico.num_conversa_nao_lidas(usuario) > 0:
                num += 1
        return num


    def __unicode__(self):
        return u'%s' % self.nome


class GrupoUsuario(models.Model):
    class Meta:
        verbose_name = "Usuário do Grupo"
        verbose_name_plural = "Usuários do Grupo"
        unique_together = (('grupo', 'usuario', ), )

    grupo = models.ForeignKey(Grupo)
    usuario = models.ForeignKey(User)
    admin = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s/%s' % (self.grupo, self.usuario)
@receiver(signals.post_save, sender=GrupoUsuario)
def create_topicousuario_grupousuario_save(sender, instance, created, raw, using, *args, **kwargs):
    for topico in instance.grupo.topico_set.filter(status='A'):
        if not topico.topicoouvinte_set.filter(ouvinte=instance.usuario):
            TopicoOuvinte.objects.create(topico=topico, ouvinte=instance.usuario)


class GrupoCategoria(models.Model):
    class Meta:
        verbose_name = u'Categoria'
        verbose_name_plural = u'Categorias'
        ordering = ('descricao', )

    grupo = models.ForeignKey(Grupo)
    descricao = models.CharField(u'Descrição', max_length=60)

    def __unicode__(self):
        return u'%s' % self.descricao


STATUS_TOPICO = (
    ('A', u'Aberto'),
    ('F', u'Fechado'),
)
class Topico(models.Model):
    class Meta:
        verbose_name = u'Tópico'
        verbose_name_plural = u'Tópicos'
        ordering = ('-dt_ultima_atualizacao', )

    titulo = models.CharField(u'Título', max_length=200)
    grupo = models.ForeignKey(Grupo)
    status = models.CharField(u'Status', max_length=1, choices=STATUS_TOPICO, default='A')
    criador = models.ForeignKey(User)
    dt_criacao = models.DateTimeField(u"Criação", auto_now_add=True)
    dt_ultima_atualizacao = models.DateTimeField(u"Ultima atualização", blank=True, null=True)
    visitacoes = models.IntegerField(default=0)
    categoria = ChainedForeignKey(GrupoCategoria, chained_fields={'grupo': 'grupo', }, show_all=False, auto_choose=False, verbose_name=u'Categoria', null=True, blank=True)

    def editavel(self):
        return self.status == 'A'

    def get_absolute_url(self):
        return reverse('forum_topico', kwargs={'grupo_pk': self.grupo.pk, 'pk': self.pk, })

    def num_comentarios(self):
        return self.conversa_set.count()-1

    def num_participantes(self):
        return len(set(list(self.conversa_set.all().values_list('autor', flat=True))))

    def num_conversa_nao_lidas(self, usuario):
        try:
            topico_ouvinte = self.topicoouvinte_set.get(ouvinte=usuario)
        except TopicoOuvinte.DoesNotExist:
            topico_ouvinte = TopicoOuvinte(
                topico=self,
                ouvinte=usuario
            )
            topico_ouvinte.save()
        return self.conversa_set.filter(dt_criacao__gt=topico_ouvinte.dtleitura).count()

    def __unicode__(self):
        return u'%s' % self.titulo
@receiver(signals.post_save, sender=Topico)
def create_topicousuario_topico_save(sender, instance, created, raw, using, *args, **kwargs):
    for grupo_usuario in instance.grupo.grupousuario_set.all():
        if not instance.topicoouvinte_set.filter(ouvinte=grupo_usuario.usuario):
            TopicoOuvinte.objects.create(topico=instance, ouvinte=grupo_usuario.usuario)


STATUS_NOTIFICACAO = (
    ('I', u'Sempre receber notificações'),
    ('R', u'Resumo Diário'),
    ('V', u'Apenas notificações de votação'),
    ('N', u'Não receber notificações'),
)

class TopicoOuvinte(models.Model):
    class Meta:
        verbose_name = u'Participante'
        verbose_name_plural = u'Participantes'
        unique_together = (('topico', 'ouvinte', ), )

    topico = models.ForeignKey(Topico)
    ouvinte = models.ForeignKey(User)
    notificacao = models.CharField(u'Tipo de Notificação', max_length=1, choices=STATUS_NOTIFICACAO, default='N')
    dtentrada = models.DateTimeField(u'Data de criação', auto_now_add=True)
    dtleitura = models.DateTimeField(u'Data de leitura', default=datetime(day=1, month=1, year=2001))
    dtnotificacao = models.DateTimeField(u'Data de notificação', default=datetime(day=1, month=1, year=2001))

    def __unicode__(self):
        return u'%s/%s' % (self.topico, self.ouvinte)


class Conversa(models.Model):
    class Meta:
        ordering = ('dt_criacao', )

    topico = models.ForeignKey(Topico)
    autor = models.ForeignKey(User)
    texto = models.TextField()
    dt_criacao = models.DateTimeField(u'Data de criação', auto_now_add=True)
    arquivo = models.FileField('Arquivo opcional com descrição ', upload_to='forum', blank=True, null=True, storage=UuidFileSystemStorage())
    conversa_pai = models.ForeignKey('self', blank=True, null=True)

    def has_delete(self, user):
        if user != self.autor or Conversa.objects.filter(conversa_pai=self).exists():
            return False
        return True

    def curtidas(self):
        queryset = []
        for status, display in STATUS_CURTIDA:
            queryset.append({
                'status': status,
                'display': display,
                'queryset': self.conversacurtida_set.filter(curtida=status),
            })
        return queryset

    def get_absolute_url(self):
        return u'%s#conversa-%s' % (reverse('forum_topico', kwargs={'grupo_pk': self.topico.grupo.pk, 'pk': self.topico.pk, }), self.pk)

    def __unicode__(self):
        return u'%s (%s)' % (self.topico, self.autor)
@receiver(signals.post_save, sender=Conversa)
def update_topico(sender, instance, created, raw, using, *args, **kwargs):
    instance.topico.dt_ultima_atualizacao = datetime.now()
    instance.topico.save()
@receiver(signals.post_save, sender=Conversa)
def enviar_notificacao_emails_topico(sender, instance, created, raw, using, *args, **kwargs):
    for ouvinte in instance.topico.topicoouvinte_set.exclude(ouvinte=instance.autor).filter(notificacao='I', dtnotificacao__lte=datetime.now()+timedelta(hours=1)):
        sendmail(
            subject=u'Tópico %s atualizado no grupo %s' % (instance.topico, instance.topico.grupo),
            to=[ouvinte.ouvinte.email, ],
            template='forum/emails/notificacao.html',
            params={
                'conversa': instance,
                'ouvinte': ouvinte,
                'host': settings.SITE_HOST,
            },
        )
        ouvinte.dtnotificacao = datetime.now()
        ouvinte.save()
@receiver(signals.post_save, sender=Conversa)
def telegram_notificacao_topico(sender, instance, created, raw, using, *args, **kwargs):
    for ouvinte in instance.topico.topicoouvinte_set.exclude(ouvinte=instance.autor).filter(notificacao='I'):
        if ouvinte.ouvinte.membro.exists():
            membro = ouvinte.ouvinte.membro.all()[0]
            if membro.telegram_id:
                mensagem = u'Tópico %s atualizado no grupo %s. Clique no link abaixo para ler o tópico: %s%s' % (
                    instance.topico,
                    instance.topico.grupo,
                    settings.SITE_HOST,
                    instance.get_absolute_url()
                )
                bot.sendMessage(membro.telegram_id, mensagem)

STATUS_CURTIDA = (
    ('I', u'Ciente'),
    ('C', u'Concordo'),
    ('P', u'Concordo em parte'),
    ('N', u'Discordo'),
)
class ConversaCurtida(models.Model):
    conversa = models.ForeignKey(Conversa)
    colaborador = models.ForeignKey(User)
    curtida = models.CharField(u'Curtiu?', max_length=1, choices=STATUS_CURTIDA)

    def __unicode__(self):
        return u'%s (%s) - %s' % (self.conversa, self.colaborador, self.get_curtida_display(), )

class ConversaMencao(models.Model):
    conversa = models.ForeignKey(Conversa)
    colaborador = models.ForeignKey(User, related_name='conversao_colaborador_set')
    mencao = models.ForeignKey(User, related_name='conversao_mencao_set')

    def __unicode__(self):
        return u'%s (%s/%s)' % (self.conversa, self.colaborador, self.mencao, )

@receiver(signals.post_save, sender=ConversaMencao)
def enviar_notificacao_emails_mencao(sender, instance, created, raw, using, *args, **kwargs):
    if created and not TopicoOuvinte.objects.filter(topico=instance.conversa.topico, ouvinte=instance.mencao, notificacao='N').exists():
        sendmail(
            subject=u'%s pediu sua atenção na Teia Digital!' % instance.colaborador,
            to=[instance.mencao.email, ],
            template='forum/emails/mencao.html',
            params={
                'mencao': instance,
                'host': settings.SITE_HOST,
            },
        )
@receiver(signals.post_save, sender=ConversaMencao)
def telegram_mention_mencao(sender, instance, created, raw, using, *args, **kwargs):
    if created:# and not TopicoOuvinte.objects.filter(topico=instance.conversa.topico, ouvinte=instance.mencao, notificacao='N').exists():
        if instance.mencao.membro.exists():
            membro = instance.mencao.membro.all()[0]
            if membro.telegram_id:
                mensagem = u'%s pediu sua atenção na Teia Digital. Clique para ler o tópico: %s%s' % (
                    instance.colaborador,
                    settings.SITE_HOST,
                    instance.conversa.get_absolute_url()
                )
                bot.sendMessage(membro.telegram_id, mensagem)

# Conversa sujeita a votação
STATUS_PROPOSTA = (
    ('A', u'Aberto'),
    ('F', u'Fechado'),
)
class Proposta(Conversa):
    dt_encerramento = models.DateTimeField(u'Data de encerramento')
    status = models.CharField(u'Situação', max_length=1, choices=STATUS_PROPOSTA)

    def __unicode__(self):
        return u'%s (%s) - %s' % (self.topico, self.autor, self.get_status_display(), )

# Voto na proposta
TIPO_VOTO =  (
    ('A', u'De acordo'),
    ('S', u'Abstém'),
    ('D', u'Em desacordo'),
    ('B', u'Bloqueia'),
)
class Voto(models.Model):
    proposta = models.ForeignKey(Proposta)
    eleitor = models.ForeignKey(User)
    voto = models.CharField(u'Tipo de Votação', max_length=1, choices=TIPO_VOTO)

    def __unicode__(self):
        return u'%s (%s) - %s' % (self.proposta, self.eleitor, self.get_voto_display(), )
