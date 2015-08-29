# coding:utf-8
from datetime import datetime, timedelta, date

from django.db import models
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db.models import signals
from django.dispatch import receiver

from municipios.models import UF
from utils.storage import UuidFileSystemStorage
#from smart_selects.db_fields import ChainedForeignKey
#from utils.models import BRDateField, BRDecimalField
#from utils.email import sendmail

GENDER = (
    ('M', u'Masculino'),
    ('F', u'Feminino'),
    ('O', u'Outros'),
)

STATUS_EMAIL = (
    ('A', u'Ativo'),
    ('N', u'Não confirmado'),
    ('S', u'SPAM'),
    ('I', u'Inválido'),
    ('O', u'Opt-out'),
)

class Pessoa(models.Model):
    class Meta:
        ordering = ['nome',]

    nome = models.CharField(u'Nome Completo',max_length=150)
    uf = models.ForeignKey(UF)
    municipio = models.CharField(u'Município', max_length=150)
    email = models.EmailField(u'Email')
    sexo = models.CharField(max_length=1, choices=GENDER, default='O')
    celular = models.CharField(max_length=14, blank=True, null=True, help_text=u'Ex.: (XX)XXXXX-XXXX')
    residencial = models.CharField(max_length=14, blank=True, null=True, help_text=u'Ex.: (XX)XXXXX-XXXX')
    dtcadastro = models.DateField(u'Dt.Cadastro', blank=True, default=datetime.now)
    status_email = models.CharField(max_length=1, choices=STATUS_EMAIL, default='A')

    def __unicode__(self):
        return u'%s (%s)' % (self.nome, self.email)

class Membro(Pessoa):
    class Meta:
        ordering = ['nome',]
        verbose_name = u'Colaborador'
        verbose_name_plural = u'Colaboradores'

    atividade_profissional = models.CharField(u'Atividade Profissional', max_length=150, blank=True, null=True)
    dtnascimento = models.DateField(u'Dt.Nascimento', blank=True, null=True)
    rg = models.CharField(u'RG', max_length=50, blank=True, null=True)
    cpf = models.CharField(u'CPF', max_length=14, blank=True, null=True)
    uf_eleitoral = models.ForeignKey(UF, verbose_name=u'UF do Domicílio Eleitoral', blank=True, null=True)
    municipio_eleitoral= models.CharField(u'Município Eleitoral', max_length=150, blank=True, null=True)
    zona_eleitoral= models.CharField(u'Zona', max_length=3, blank=True, null=True)
    secao_eleitoral= models.CharField(u'Seção', max_length=4, blank=True, null=True)
    titulo_eleitoral = models.CharField(u'Título', max_length=50, blank=True, null=True)
    nome_da_mae = models.CharField(u'Nome da mãe', max_length=60, blank=True, null=True)
    filiacao_partidaria = models.CharField(u'Filiação Partidária', max_length=100, blank=True, null=True)
    usuario = models.ForeignKey(User, related_name='membro', verbose_name=u'Usuário', blank=True, null=True)
    facebook_id = models.CharField(u'Facebook ID', max_length=120, editable=False, blank=True, null=True)
    facebook_access_token = models.TextField(editable=False, blank=True, null=True)
    aprovador = models.ForeignKey(User, related_name='membro_aprovador', verbose_name=u'Aprovador', blank=True, null=True)
    filiado = models.BooleanField(u'É filiado?', default=False)

    def save(self, *args, **kwargs):
        super(Membro, self).save(*args, **kwargs)
        if not self.aprovador:
            return

        if not self.usuario:
            grupo = Group.objects.get_or_create(name=u'Colaborador')[0]
            login = self.email.split('@')[0]
            cont = 1
            while User.objects.filter(username=login).count() > 0:
                login = login + (u'%d' % cont)
                cont += 1
            self.usuario = User.objects.create_user(login, self.email, 'raiz#2015')
            self.usuario.is_active = True
            self.usuario.is_staff = True
            self.usuario.first_name = self.nome
            self.usuario.groups.add(grupo)
            self.usuario.save()
            super(Membro, self).save(*args, **kwargs)
        else:
            if self.usuario.email != self.email:
                self.usuario.email = self.email
                self.usuario.save()

CIRCULO_TIPO = (
    ('R', u'Círculo Regional'),
    ('G', u'Grupo de Trabalho (GT)'),
    ('T', u'Círculo Temático'),
    ('I', u'Círculo Identitários'),
)

CIRCULO_STATUS = (
    ('A', u'Ativo'),
    ('I', u'Desativado'),
)

class Circulo(models.Model):
    class Meta:
        verbose_name = u'Grupo'

    titulo = models.CharField(u'Título', max_length=80)
    descricao = models.TextField(u'Descricao') # HTML
    tipo = models.CharField(u'Tipo', max_length=1, choices=CIRCULO_TIPO)
    uf = models.ForeignKey(UF, blank=True, null=True)
    municipio = models.CharField(u'Município', max_length=150, blank=True, null=True)
    oficial = models.BooleanField(u'Oficial', default=False)
    dtcadastro = models.DateField(u'Dt.Cadastro', default=datetime.now)
    site_externo = models.URLField(u'Site / Blog / Fanpage', blank=True, null=True)
    imagem = models.FileField(u'Imagem ou Logo do grupo', blank=True, null=True,
        upload_to='circulo', storage=UuidFileSystemStorage())
    status = models.CharField('Situação', max_length=1, choices=CIRCULO_STATUS, default='A')

    def __unicode__(self):
        return u'%s %s' % (self.get_tipo_display(), self.titulo)

class CirculoMembro(models.Model):
    class Meta:
        verbose_name = u'Colaborador do Círculo'
        verbose_name_plural = u'Colaboradores do Círculo'

    circulo = models.ForeignKey(Circulo)
    membro = models.ForeignKey(Membro)
    administrador = models.BooleanField(default=False)
#    tipo_alerta = models.CharField(u'Recebimento de Notificações') # Frequência de recebimento de alertas
#    representante = models.ForeignKey(Membro) # Membro que representa alguém no Círculo

# Só mostrar o campo Oficial se o usuário for do grupo Diretoria
# Só permitir a edição do evento se o membro for administrador do círculo
    def __unicode__(self):
        return u'#%s' % self.pk

# Eventos que devem ser divulgados no site
class CirculoEvento(models.Model):
    circulo = models.ForeignKey(Circulo)
    nome = models.CharField(u'Título', max_length=100)
    dt_evento = models.DateTimeField(u'Dt.Evento')
    local = models.TextField(u'Local do Evento')

    def __unicode__(self):
        return u'%s' % self.nome

    class Meta:
        verbose_name = u'Evento do Círculo'
        verbose_name_plural = u'Eventos dos círculos'

# Fóruns - Baseado no modelo de dados do Loomio
'''
def formata_arquivo_forum(objeto, nome_arquivo):
    nome, extensao = os.path.splitext(nome_arquivo)
    return os.path.join('forum', str(uuid.uuid4()) + extensao.lower())

STATUS_DISCUSSAO = (
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

TIPO_CURTIDA = (
    ('C', u'Curtiu'),
    ('N', u'Não curtiu'),
    )

class Topico(models.Model):
    titulo = models.CharField(u'Título', max_length=200)
    grupo = models.ForeignKey(Circulo)
    status = models.CharField(u'Status', max_length=1, choices=STATUS_DISCUSSAO)
    dt_ultima_atualizacao = models.DateTimeField(u"Ultima atualização", blank=True, null=True)
    visitacoes = models.IntegerField(default=0)
    criador = models.ForeignKey(Membro)

    class Meta:
        verbose_name = u'Tópico'
        verbose_name_plural = u'Tópicos'

class TopicoOuvinte(models.Model):
    topico = models.ForeignKey(Topico)
    ouvinte = models.ForeignKey(Colaborador)
    notificacao = models.CharField(u'Tipo de Notificação', max_length=1, choices=STATUS_NOTIFICACAO)
    dtentrada = models.DateTimeField(u'Data de criação', auto_now_add=True)

    class Meta:
        verbose_name = u'Participante'
        verbose_name_plural = u'Participantes'

class Conversa(models.Model):
    topico = models.ForeignKey(Topico)
    autor = models.ForeignKey(Membro)
    texto = models.TextField()
    dt_criacao = models.DateTimeField(u'Data de criação', auto_now_add=True)
    arquivo = models.FileField('Arquivo opcional com descrição ',upload_to=formata_arquivo_forum, blank=True, null=True)
    conversa_pai = ForeignKey('Conversa')

class ConversaCurtida(models.Model):
    conversa = models.ForeignKey(Conversa)
    colaborador = models.ForeignKey(Colaborador)
    curtida = models.CharField(u'', max_length=1, choices=STATUS_CURTIDA)

# Conversa sujeita a votação
class Proposta(Conversa):
    dt_encerramento = models.DateTimeField(u'Data de encerramento')
    status = models.CharField(u'Situação', max_length=1, choices=STATUS_PROPOSTA)

# Voto na proposta
class Voto(models.Model):
    discussao = models.ForeignKey(Proposta)
    eleitor = models.ForeignKey(Membro)
    voto = models.CharField(u'Tipo de Votação',max_length=1, choices=TIPO_VOTO)

'''
