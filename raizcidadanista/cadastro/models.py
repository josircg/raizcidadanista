# coding:utf-8
from datetime import datetime, timedelta, date
from decimal import Decimal

from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.db.models import signals, F
from django.dispatch import receiver

from django.utils.http import int_to_base36
from django.utils.crypto import salted_hmac

from django.core.mail import EmailMultiAlternatives
from django.template.defaultfilters import slugify
from django.template.loader import get_template
from django.template import Template
from django.template.context import Context
from threading import Thread
from time import sleep

from municipios.models import UF, Municipio
from forum.models import Grupo, GrupoUsuario
from cms.models import Article, Section, SectionItem, URLMigrate
from utils.storage import UuidFileSystemStorage
from cms.email import sendmail, send_email_thread
from smart_selects.db_fields import ChainedForeignKey
from utils.fields import BRDecimalField


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
    ('O', u'Cancelado'),
)

class Pessoa(models.Model):
    class Meta:
        ordering = ['nome',]

    nome = models.CharField(u'Nome Completo (tal como consta na sua identidade)', max_length=150)
    apelido = models.CharField(u'Apelido ou Alcunha', max_length=30, blank=True, null=True)
    email = models.EmailField(u'Email', blank=True, null=True )
    uf = models.ForeignKey(UF, verbose_name='UF')
    municipio = models.CharField(u'Município', max_length=150, blank=True, null=True)
    sexo = models.CharField(max_length=1, choices=GENDER, default='O')
    celular = models.CharField(u'Tel.Celular', max_length=14, blank=True, null=True, help_text=u'Ex.: (XX)XXXXX-XXXX')
    residencial = models.CharField(u'Tel.Residencial', max_length=14, blank=True, null=True, help_text=u'Ex.: (XX)XXXXX-XXXX')
    dtcadastro = models.DateField(u'Dt.Cadastro', blank=True, default=datetime.now)
    status_email = models.CharField(max_length=1, choices=STATUS_EMAIL, default='N')

    ('I', u'Inválido'),

    def __unicode__(self):
        return u'%s' % self.nome

    def save(self, *args, **kwargs):
        if self.email is None:
            self.status_email = 'I'
        super(Pessoa, self).save(*args, **kwargs)


@receiver(signals.post_save, sender=Pessoa)
def validaremail_pessoa_signal(sender, instance, created, raw, using, *args, **kwargs):
    if created and (instance.status_email is None or instance.status_email == 'N'):
        sendmail(
            subject=u'Raiz Movimento Cidadanista - Validação de email',
            to=[instance.email, ],
            template='emails/validar-email.html',
            params={
                'pessoa': instance,
                'SITE_HOST': settings.SITE_HOST,
            },
        )

class Membro(Pessoa):
    class Meta:
        ordering = ['nome',]
        verbose_name = u'Colaborador'
        verbose_name_plural = u'Colaboradores'

    TIPO_CONTRIBUICAO = (
        ('1', u'Mensal'),
        ('3', u'Trimestral'),
        ('6', u'Semestral'),
        ('A', u'Anual'),
        ('O', u'Não pretende fazer'),
        ('S', u'Suspensa'),
        ('N', u'Não definida'),
    )

    ESTADO_CIVIL = (
        ('S', u'Solteira(o)'),
        ('C', u'Casada(o)'),
        ('E', u'Separada(o)'),
        ('D', u'Divorciada(o)'),
        ('V', u'Viúva(o)'),
    )

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
    twitter_id = models.CharField(u'Twitter ID', max_length=120, editable=False, blank=True, null=True)
    twitter_oauth_token = models.TextField(editable=False, blank=True, null=True)
    twitter_oauth_token_secret = models.TextField(editable=False, blank=True, null=True)
    telegram_id = models.CharField(u'Telegram ID', max_length=120, editable=False, blank=True, null=True)
    aprovador = models.ForeignKey(User, related_name='membro_aprovador', verbose_name=u'Aprovador', blank=True, null=True)
    filiado = models.BooleanField(u'Pretende ser filiado?', default=False)
    dt_prefiliacao = models.DateField(u'Dt de pré-filiação', blank=True, null=True)
    contrib_tipo = models.CharField(u'Tipo de Contribuição', max_length=1, choices=TIPO_CONTRIBUICAO, default='N')
    contrib_valor = BRDecimalField(u'Valor da Contribuição', max_digits=7, decimal_places=2, default=0)
    contrib_prox_pgto = models.DateField(u'Próximo Pagamento', blank=True, null=True)
    estadocivil = models.CharField(u'Estado civil', max_length=1, choices=ESTADO_CIVIL, blank=True, null=True)
    endereco_cep = models.CharField(u'CEP', max_length=9, blank=True, null=True)
    endereco = models.CharField(u'Endereço', max_length=100, blank=True, null=True)
    endereco_num = models.CharField(u'Nº', max_length=10, blank=True, null=True)
    endereco_complemento = models.CharField(u'Complemento', max_length=20, blank=True, null=True)
    uf_naturalidade = models.ForeignKey(UF, verbose_name='Naturalidade: UF', related_name='uf_naturalidade', null=True, blank=True)
    municipio_naturalidade = models.CharField(u'Naturalidade: Município', max_length=150, blank=True, null=True)
    fundador = models.BooleanField(u'Quero assinar a ata de fundação da RAiZ', default=False)
    assinado = models.BooleanField(u'Requerimento assinado', default=False)

    def vr_apagar(self, data):
        if self.contrib_prox_pgto and (self.contrib_prox_pgto.month == data.month and self.contrib_prox_pgto.year == data.year):
            return self.contrib_valor
        elif self.contrib_prox_pgto and self.contrib_prox_pgto > data:
            return Decimal(0.0)
        return self.contrib_valor

    def get_estadocivil_genero_display(self):
        if self.sexo == 'F':
            return self.get_estadocivil_display().replace('a(o)', 'a')
        elif self.sexo == 'M':
            return self.get_estadocivil_display().replace('a(o)', 'o')
        else:
            return self.get_estadocivil_display()

    def nacionalidade(self):
        if self.uf_naturalidade:
            if self.sexo == 'M':
                return 'brasileiro,'
            elif self.sexo == 'F':
                return 'brasileira,'
            else:
                return 'brasileira(o),'
        else:
            return ''

    def naturalidade(self):
        if self.uf_naturalidade:
            return 'natural de %s/%s' % (self.municipio_naturalidade, self.uf_naturalidade.uf)
        else:
            if self.municipio_naturalidade:
                return 'natural de %s' % (self.municipio_naturalidade)
            else:
                return 'natural de %s/%s' % (self.municipio, self.uf.uf)

    def get_absolute_update_url(self):
        def create_token(membro):
            key_salt = "cadastro.forms.AtualizarCadastroLinkForm"
            value = u'%s%s' % (membro.pk, membro.email)
            return salted_hmac(key_salt, value).hexdigest()[::2]

        return reverse('atualizar_cadastro', kwargs={
            'uidb36': int_to_base36(self.pk),
            'ts_b36': int_to_base36((date.today() - date(2001, 1, 1)).days),
            'token': create_token(self),
        })

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
            self.usuario.first_name = self.nome.split(' ')[0]
            self.usuario.groups.add(grupo)
            self.usuario.save()
            super(Membro, self).save(*args, **kwargs)
        else:
            if self.usuario.email != self.email:
                self.usuario.email = self.email
                self.usuario.save()

@receiver(signals.post_save, sender=Membro)
def validaremail_membro_signal(sender, instance, created, raw, using, *args, **kwargs):
    if created and (instance.status_email is None or instance.status_email == 'N'):
        sendmail(
            subject=u'Raiz Movimento Cidadanista - Validação de email',
            to=[instance.email, ],
            template='emails/validar-email.html',
            params={
                'pessoa': instance,
                'SITE_HOST': settings.SITE_HOST,
            },
        )
@receiver(signals.pre_save, sender=Membro)
def update_dt_prefiliacao_membro_signal(sender, instance, raw, using, *args, **kwargs):
    if not instance.dt_prefiliacao:
        instance.dt_prefiliacao = date.today()
@receiver(signals.post_save, sender=Membro)
def add_circulo_membro_signal(sender, instance, created, raw, using, *args, **kwargs):
    if created:
        circulos_ja_cadastrados_pks = CirculoMembro.objects.filter(membro=instance).values_list('circulo', flat=True)
        circulos_estaduais_municipais = Circulo.objects.filter(uf=instance.uf, tipo__in=('R', 'S'), municipio__in=(None, '', instance.municipio)).exclude(pk__in=circulos_ja_cadastrados_pks)
        for circulo in circulos_estaduais_municipais:
            CirculoMembro(circulo=circulo, membro=instance).save()

            # Log
            user = User.objects.get_or_create(username="sys")[0]
            # Log do membro
            LogEntry.objects.log_action(
                user_id = user.pk,
                content_type_id = ContentType.objects.get_for_model(instance).pk,
                object_id = instance.pk,
                object_repr = u"%s" % instance,
                action_flag = CHANGE,
                change_message = u'Membro adicionado automaticamente no Círculo %s.' % circulo
            )
            # Log do Círculo
            LogEntry.objects.log_action(
                user_id = user.pk,
                content_type_id = ContentType.objects.get_for_model(circulo).pk,
                object_id = circulo.pk,
                object_repr = u"%s" % circulo,
                action_flag = CHANGE,
                change_message = u'Membro %s adicionado automaticamente.' % instance
            )


class Filiado(Membro):
    class Meta:
        proxy = True

CIRCULO_TIPO = (
    ('R', u'Círculo Regional'),
    ('C', u'Coordenação'),
    ('G', u'Grupo de Trabalho (GT)'),
    ('T', u'Círculo Temático'),
    ('I', u'Círculo Identitários'),
    ('E', u'Esfera'),
    ('S', u'Círculo Estadual'),
)

CIRCULO_STATUS = (
    ('A', u'Ativo'),
    ('F', u'Em Formação'),
    ('G', u'Grupo de Discussão'),
    ('I', u'Inativo'),
)

class Circulo(models.Model):
    class Meta:
        verbose_name = u'Círculo/GT/Coordenação/Esfera'
        verbose_name_plural = u'Círculos e Grupos de Trabalho'
        ordering = ('tipo', 'titulo', )

    titulo = models.CharField(u'Título', max_length=80)
    slug = models.SlugField(u'Url', max_length=80, blank=True)
    descricao = models.TextField(u'Descricao') # HTML
    tipo = models.CharField(u'Tipo', max_length=1, choices=CIRCULO_TIPO)
    uf = models.ForeignKey(UF, blank=True, null=True)
    municipio = models.CharField(u'Município', max_length=150, blank=True, null=True)
    oficial = models.BooleanField(u'Oficial', default=False)
    permitecadastro = models.BooleanField(u'Permite cadastro', default=True)
    dtcadastro = models.DateField(u'Dt.Cadastro', default=datetime.now)
    site_externo = models.URLField(u'Site / Blog / Fanpage', blank=True, null=True)
    imagem = models.FileField(u'Imagem ou Logo do grupo', blank=True, null=True,
        upload_to='circulo', storage=UuidFileSystemStorage())
    status = models.CharField('Situação', max_length=1, choices=CIRCULO_STATUS, default='A')
    grupo = models.ForeignKey(Grupo, editable=False, blank=True, null=True)
    section = models.ForeignKey(Section, verbose_name=u'Seção', blank=True, null=True)

    def clean(self):
        if self.slug and self.section and URLMigrate.objects.filter(old_url=self.get_absolute_url()).exclude(new_url=self.section.get_absolute_url()).exists():
            raise ValidationError(u'Esta URL já está em uso. Informe outra url.')
        return super(Circulo, self).clean()

    def get_absolute_url(self):
        if self.section:
            return u'/%s/' % self.slug
        return self.site_externo
    get_absolute_url.short_description = u'URL'

    def get_absolute_entrar_url(self):
        return reverse('membro_entrar_circulo', kwargs={'circulo_id': self.pk, })

    def administrador_publico(self):
        return self.circulomembro_set.filter(publico=True, administrador=True)

    def num_membros(self):
        return self.circulomembro_set.count()
    num_membros.short_description = u'Nº de membros'

    def __unicode__(self):
        return u'%s %s' % (self.get_tipo_display(), self.titulo)
@receiver(signals.pre_save, sender=Circulo)
def circulo_slug_pre_save(sender, instance, raw, using, *args, **kwargs):
    if not instance.slug:
        slug = slugify(instance.titulo)
        new_slug = slug
        counter = 0
        while sender.objects.filter(slug=new_slug).exclude(id=instance.id).count() > 0:
            counter += 1
            new_slug = '%s-%d'%(slug, counter)
        instance.slug = new_slug


class CirculoMembro(models.Model):
    class Meta:
        verbose_name = u'Colaborador do Círculo/GT'
        verbose_name_plural = u'Colaboradores do Círculo/GT'
        unique_together = (('circulo', 'membro', ), )

    circulo = models.ForeignKey(Circulo)
    membro = models.ForeignKey(Membro)
    administrador = models.BooleanField(default=False)
    publico = models.BooleanField(u'Público', default=False)
    grupousuario = models.ForeignKey(GrupoUsuario, editable=False, blank=True, null=True)

    def celular(self):
        return self.membro.celular
    celular.short_description = u'Tel.Celular'

    def residencial(self):
        return self.membro.residencial
    residencial.short_description = u'Tel.Residencial'

    def is_filiado(self):
        return self.membro.filiado
    is_filiado.short_description = u'Filiado'
    is_filiado.boolean = True
#    tipo_alerta = models.CharField(u'Recebimento de Notificações') # Frequência de recebimento de alertas
#    representante = models.ForeignKey(Membro) # Membro que representa alguém no Círculo

# Só mostrar o campo Oficial se o usuário for do grupo Diretoria
# Só permitir a edição do evento se o membro for administrador do círculo
    def __unicode__(self):
        return u'%s (%s)' % (self.circulo, self.membro)
@receiver(signals.pre_save, sender=CirculoMembro)
def cria_grupousuario_circulomemebro_signal(sender, instance, raw, using, *args, **kwargs):
    if instance.circulo.grupo and instance.membro.usuario and not instance.grupousuario:
        instance.grupousuario = GrupoUsuario.objects.get_or_create(grupo=instance.circulo.grupo, usuario=instance.membro.usuario)[0]
    if instance.grupousuario:
        instance.grupousuario.admin = instance.administrador
        instance.grupousuario.save()
@receiver(signals.post_delete, sender=CirculoMembro)
def remove_grupousuario_circulomemebro_signal(sender, instance, using, *args, **kwargs):
    if instance.grupousuario:
        try: instance.grupousuario.delete()
        except: pass
@receiver(signals.post_save, sender=CirculoMembro)
def udpdate_user_circulomemebro_signal(sender, instance, raw, using, *args, **kwargs):
    if instance.membro.usuario:
        if CirculoMembro.objects.filter(membro=instance.membro, administrador=True).exists():
            instance.membro.usuario.groups.add(Group.objects.get_or_create(name=u'Coordenador Local')[0])
        else:
            instance.membro.usuario.groups.remove(Group.objects.get_or_create(name=u'Coordenador Local')[0])


# Eventos que devem ser divulgados no site
class CirculoEvento(models.Model):
    circulo = models.ForeignKey(Circulo)
    nome = models.CharField(u'Título', max_length=100)
    dt_evento = models.DateTimeField(u'Dt.Evento')
    local = models.TextField(u'Descrição e Local')
    privado = models.BooleanField(u'Privado', default=True)
    artigo = models.ForeignKey(Article, editable=False, blank=True, null=True)

    def __unicode__(self):
        return u'%s' % self.nome

    class Meta:
        verbose_name = u'Evento do Círculo'
        verbose_name_plural = u'Eventos dos círculos'
@receiver(signals.pre_save, sender=CirculoEvento)
def create_article_evento_signal(sender, instance, raw, using, *args, **kwargs):
    if not instance.privado and not instance.artigo:
        # Cria o artigo
        try:
            section = Section.objects.get(slug='eventos')
        except Section.DoesNotExist:
            section = Section.objects.create(title='Eventos', slug='eventos')
        author = User.objects.get_or_create(username="sys")[0]
        artigo = Article(
            title=u'%s - %s' % (instance.circulo.titulo, instance.nome,),
            header=instance.local.replace('\n', '<br>'),
            content=instance.local.replace('\n', '<br>'),
            author=author,
            created_at=instance.dt_evento,
            is_active=True,
        )
        artigo.save()
        SectionItem(section=section, article=artigo).save()
        if instance.circulo.section:
            SectionItem(section=instance.circulo.section, article=artigo).save()
        # Vincula o artigo ao CirculoEvento
        instance.artigo = artigo
    if instance.artigo:
        # Desabilita/Havilita a visualização do artigo
        instance.artigo.header = instance.local.replace('\n', '<br>')
        instance.artigo.content = instance.local.replace('\n', '<br>')
        instance.artigo.is_active = not instance.privado
        instance.artigo.created_at = instance.dt_evento
        instance.artigo.save()


STATUS_LISTA = (
    ('A', u'Ativo'),
    ('P', u'Privado'),
    ('I', u'Inativo'),
)
class Lista(models.Model):
    nome = models.CharField(max_length=100)
    validade = models.DateField(u'Data Limite para cadastro')
    status = models.CharField(max_length=1, choices=STATUS_LISTA, default=u'A')
    seo = models.TextField('SEO Content', blank=True, null=True)
    analytics = models.TextField('Analytics', blank=True, null=True)

    def num_cadastros(self):
        return self.listacadastro_set.count()
    num_cadastros.short_description = u"Nº de cadastros"

    def __unicode__(self):
        return u"%s" % self.nome


class ListaCadastro(models.Model):
    class Meta:
        ordering = ('lista', 'pessoa__nome', )
        verbose_name = u'Lista › Cadastro'
        verbose_name_plural = u'Lista › Cadastros'

    lista = models.ForeignKey(Lista)
    pessoa = models.ForeignKey(Pessoa)
    dtinclusao = models.DateTimeField(u'Inclusão', auto_now_add=True)

    def __unicode__(self):
        return u"%s - %s" % (self.lista, self.pessoa)


CAMPANHA_STATUS_CHOICES = (
    ('E', u'Em edição'),
    ('P', u'Processando'),
    ('I', u'Interrompida'),
    ('R', u'Erro no Envio'),
    ('F', u'Finalizada'),
)
CAMPANHA_TIPO_CHOICES = (
    ('L', u'Lista'),
    ('M', u'Membros'),
    ('V', u'Visitantes'),
)
class Campanha(models.Model):
    class Meta:
        ordering = ('dtenvio', )

    tipo = models.CharField(u'Tipo de campanha', max_length=1, choices=CAMPANHA_TIPO_CHOICES)
    lista = models.ForeignKey(Lista, blank=True, null=True, on_delete=models.SET_NULL)
    circulo_membro = models.ForeignKey(Circulo, blank=True, null=True, on_delete=models.SET_NULL, related_name='campanha_circulo_membro', verbose_name=u'Círculo (Membros)')
    circulo_visitante = models.ForeignKey(Circulo, blank=True, null=True, on_delete=models.SET_NULL, related_name='campanha_circulo_visitante', verbose_name=u'Círculo (Visitantes)')
    autor = models.ForeignKey(User, blank=True, null=True)
    status = models.CharField(u'Status', max_length=1, choices=CAMPANHA_STATUS_CHOICES, default='E')
    dtenvio = models.DateTimeField(u'Dt. Envio', blank=True, null=True)
    assunto = models.CharField(u'Assunto', max_length=255)
    template = models.TextField(u'Template')
    qtde_envio = models.PositiveIntegerField(u'Qtd de emails enviados', default=0)
    qtde_erros = models.PositiveIntegerField(u'Qtd de emails que deu erro', default=0)
    qtde_views = models.PositiveIntegerField(u'Qtd de visualizações', default=0)

    def template_html(self):
        return u'<iframe class="html" src="%s"></iframe>' % reverse('admin:cadastro_campanha_template', kwargs={'id_campanha': self.pk,})
    template_html.allow_tags = True
    template_html.short_description = u'Template'

    def get_qtde_views_url(self):
        return reverse('campanha_views', kwargs={'pk': self.pk, })

    def fonte(self):
        if self.tipo == 'L':
            return self.lista
        elif self.tipo == 'M':
            return u'Membros do %s' % self.circulo_membro
        elif self.tipo == 'V':
            return u'Visitantes do %s' % self.circulo_visitante

    def get_email_list(self):
        if self.tipo == 'L':
            return self.lista.listacadastro_set.filter(pessoa__status_email__in=('A', 'N', )).values_list('pessoa__email', flat=True).order_by('pessoa__email')
        elif self.tipo == 'M':
            return self.circulo_membro.circulomembro_set.filter(membro__status_email__in=('A', 'N', )).values_list('membro__email', flat=True).order_by('membro__email')
        elif self.tipo == 'V':
            return CirculoMembro.objects.filter(circulo__uf=self.circulo_visitante.uf, membro__status_email__in=('A', 'N', )).values_list('membro__email', flat=True).order_by('membro__email')

    def send_email_test(self, to):
        template_content = Template(self.template)

        text_content = self.assunto
        html_content = template_content.render(Context({}))

        msg = EmailMultiAlternatives(self.assunto, text_content, settings.DEFAULT_FROM_EMAIL, to=to)
        msg.attach_alternative(html_content, 'text/html; charset=UTF-8')
        msg.send()

    def send_emails(self, user, resumir):
        def _send_campanha_thread(campanha_id, user_id, emails_list, from_email=settings.DEFAULT_FROM_EMAIL):
            def splip_emails(emails, ite=100):
                ini = 0
                for i in range(ite, len(emails), ite):
                    yield emails[ini:i]
                    ini = i
                if len(emails) > ini:
                    yield emails[ini:len(emails)]

            campanha = Campanha.objects.get(pk=campanha_id)
            subject = campanha.assunto
            text_content = subject
            campanha_ct = ContentType.objects.get_for_model(campanha)

            # Renderiza o template, se não consegui mata a thread
            template = u'%s<img src="%s%s" />' % (campanha.template, settings.SITE_HOST, campanha.get_qtde_views_url())
            try: template_content = get_template(template)
            except:
                try: template_content = Template(template)
                except:
                    LogEntry.objects.log_action(
                        user_id = user_id,
                        content_type_id = campanha_ct.pk,
                        object_id = campanha.pk,
                        object_repr = u"%s" % campanha,
                        action_flag = CHANGE,
                        change_message = u'[ERROR] Erro ao montar template para envio.'
                    )
                    Campanha.objects.filter(pk=campanha_id).update(qtde_erros=len(emails_list), status='R')
                    return
            html_content = template_content.render(Context({}))

            LogEntry.objects.log_action(
                user_id = user_id,
                content_type_id = campanha_ct.pk,
                object_id = campanha.pk,
                object_repr = u"%s" % campanha,
                action_flag = CHANGE,
                change_message = u'[INFO] Iniciado o envio de %d emails' % len(emails_list)
            )

            for emails in splip_emails(emails_list):
                # Cria a mensagem
                msg = EmailMultiAlternatives(subject, text_content, from_email, bcc=emails)
                msg.attach_alternative(html_content, 'text/html; charset=UTF-8')

                # Realiza até 3 tentativas de enviar
                tentativas = 0
                while tentativas < 3:
                    # Interromer thread caso tenha marcado o status como Interrompido
                    if Campanha.objects.get(pk=campanha_id).status == 'I':
                        LogEntry.objects.log_action(
                            user_id = user_id,
                            content_type_id = campanha_ct.pk,
                            object_id = campanha.pk,
                            object_repr = u"%s" % campanha,
                            action_flag = CHANGE,
                            change_message = u'[INFO] Processo interrompido pelo usuário.'
                        )
                        return
                    try:
                        msg.send()
                        break
                    except:
                        LogEntry.objects.log_action(
                            user_id = user_id,
                            content_type_id = campanha_ct.pk,
                            object_id = campanha.pk,
                            object_repr = u"%s" % campanha,
                            action_flag = CHANGE,
                            change_message = u'[ERROR] Falha na %sª/3 tentativa de envio para: %s.' % (tentativas+1, u", ".join(emails), )
                        )
                        tentativas += 1
                        sleep(30)

                if tentativas == 3:
                    print '[ERROR] Deu erro!'
                    LogEntry.objects.log_action(
                        user_id = user_id,
                        content_type_id = campanha_ct.pk,
                        object_id = campanha.pk,
                        object_repr = u"%s" % campanha,
                        action_flag = CHANGE,
                        change_message = u'[ERROR] Erro ao enviar emails para: %s.' % u", ".join(emails)
                    )
                    Campanha.objects.filter(pk=campanha_id).update(qtde_erros=campanha.lista.listacadastro_set.filter(pessoa__status_email__in=('A', 'N', )).count()-F('qtde_envio'), status='E')
                    return
                else:
                    # Atualiza o número de envios
                    Campanha.objects.filter(pk=campanha_id).update(qtde_envio=F('qtde_envio')+len(emails))


            LogEntry.objects.log_action(
                user_id = user_id,
                content_type_id = campanha_ct.pk,
                object_id = campanha.pk,
                object_repr = u"%s" % campanha,
                action_flag = CHANGE,
                change_message = u'[INFO] Envio Finalizado'
            )

            # Atualiza o status
            Campanha.objects.filter(pk=campanha_id).update(status='F')

        emails_list = self.get_email_list()
        if resumir == True:
            emails_list = emails_list[self.qtde_envio:]
            self.qtde_erros = 0
        self.dtenvio = datetime.now()
        self.save()

        th=Thread(target=_send_campanha_thread, kwargs={'campanha_id': self.pk, 'user_id': user.pk,  'emails_list': emails_list, })
        th.start()

    def __unicode__(self):
        return self.assunto


class ColetaArticulacao(models.Model):
    class Meta:
        verbose_name = u'Articulação da Coleta'
        verbose_name_plural = u'Articuladores da Coleta'

    UF = models.ForeignKey(UF, verbose_name=u'UF')
    municipio = ChainedForeignKey(Municipio, chained_fields={'UF': 'uf', }, show_all=False, auto_choose=False, verbose_name=u'Município', null=True, blank=True)
    zona = models.IntegerField(u'Zona', null=True, blank=True)
    articulador = models.ForeignKey(Membro, verbose_name=u'Articulador')

    def clean(self):
        if not self.municipio:
            if not self.articulador.usuario or self.articulador.usuario.groups.filter(name=u'Cadastro'):
                raise ValidationError(u'O campo Município é obrigatório para esse Articulador.')
        return super(ColetaArticulacao, self).clean()

    def articulador_email(self):
        return u'%s' % self.articulador.email
    articulador_email.short_description = u'Email do Articulador'

    def __unicode__(self):
        return u'%s: %s' % (self.UF, self.articulador.nome)


@receiver(signals.post_save, sender=ColetaArticulacao)
def articulacao_post_save(sender, instance, raw, using, *args, **kwargs):
    if instance.articulador.usuario:
        group = Group.objects.get_or_create(name=u'Articulador')[0]
        if not instance.municipio:
            instance.articulador.usuario.groups.add(group)
            instance.articulador.usuario.save()
        else:
            instance.articulador.usuario.groups.remove(group)
            instance.articulador.usuario.save()

CANDIDATURA_CARGO = (
    ('P', u'Prefeito'),
    ('V', u'Vereador'),
)

class Coligacao(models.Model):
    class Meta:
        verbose_name = u'Coligação'
        verbose_name_plural = u'Coligações'

    UF = models.ForeignKey(UF, verbose_name=u'UF')
    municipio = ChainedForeignKey(Municipio, chained_fields={'UF': 'uf', }, show_all=False, auto_choose=False, verbose_name=u'Município')
    partidos = models.CharField(u'Partidos',max_length=50, blank=True, null=True)

    def __unicode__(self):
        return u'%s/%s: %s' % (self.UF, self.municipio, self.partidos)

class Candidatura(models.Model):
    coligacao = models.ForeignKey(Coligacao)
    candidato = models.ForeignKey(Membro, verbose_name=u'Candidata/o')
    partido = models.CharField(max_length=50)
    cargo = models.CharField(max_length=1, choices=CANDIDATURA_CARGO)
    eleito = models.BooleanField()

    def __unicode__(self):
        return u'%s (%s)' % (self.candidato.nome, self.coligacao)

class ArticleCadastro(Article):
    class Meta:
        proxy = True
        verbose_name = u'Artigo dos Grupos'
        verbose_name_plural = u'Artigos dos Grupos'
