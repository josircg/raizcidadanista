# coding:utf-8
from datetime import datetime, timedelta, date
from decimal import Decimal

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
from time import sleep

from municipios.models import UF
from forum.models import Grupo, GrupoUsuario
from utils.storage import UuidFileSystemStorage
from cms.email import sendmail, send_email_thread
#from smart_selects.db_fields import ChainedForeignKey
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
    ('O', u'Opt-out'),
)

class Pessoa(models.Model):
    class Meta:
        ordering = ['nome',]

    nome = models.CharField(u'Nome Completo',max_length=150)
    email = models.EmailField(u'Email')
    uf = models.ForeignKey(UF)
    municipio = models.CharField(u'Município', max_length=150, blank=True, null=True)
    sexo = models.CharField(max_length=1, choices=GENDER, default='O')
    celular = models.CharField(max_length=14, blank=True, null=True, help_text=u'Ex.: (XX)XXXXX-XXXX')
    residencial = models.CharField(max_length=14, blank=True, null=True, help_text=u'Ex.: (XX)XXXXX-XXXX')
    dtcadastro = models.DateField(u'Dt.Cadastro', blank=True, default=datetime.now)
    status_email = models.CharField(max_length=1, choices=STATUS_EMAIL, default='N')

    def __unicode__(self):
        return u'%s (%s)' % (self.nome, self.email)

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
    aprovador = models.ForeignKey(User, related_name='membro_aprovador', verbose_name=u'Aprovador', blank=True, null=True)
    filiado = models.BooleanField(u'Pretende ser filiado?', default=False)
    dt_prefiliacao = models.DateField(u'Dt de pré-filiação', blank=True, null=True)
    contrib_tipo = models.CharField(u'Tipo de Contribuição', max_length=1, choices=TIPO_CONTRIBUICAO, default='N')
    contrib_valor = BRDecimalField(u'Valor da Contribuição', max_digits=7, decimal_places=2, default=0)
    contrib_prox_pgto = models.DateField(u'Próximo Pagamento', blank=True, null=True)

    def vr_apagar(self, data):
        if self.contrib_prox_pgto and (self.contrib_prox_pgto.month == data.month and self.contrib_prox_pgto.year == data.year):
            return self.contrib_valor
        elif self.contrib_prox_pgto and self.contrib_prox_pgto > data:
            return Decimal(0.0)
        return self.contrib_valor

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

class Filiado(Membro):
    class Meta:
        proxy = True

CIRCULO_TIPO = (
    ('R', u'Círculo Regional'),
    ('G', u'Grupo de Trabalho (GT)'),
    ('T', u'Círculo Temático'),
    ('I', u'Círculo Identitários'),
    ('E', u'Esfera'),
)

CIRCULO_STATUS = (
    ('A', u'Ativo'),
    ('I', u'Desativado'),
)

class Circulo(models.Model):
    class Meta:
        verbose_name = u'Círculo/Esfera/GT'
        verbose_name_plural = u'Círculos e Grupos de Trabalho'
        ordering = ('tipo', 'titulo', )

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
    grupo = models.ForeignKey(Grupo, editable=False, blank=True, null=True)

    def get_absolute_entrar_url(self):
        return reverse('membro_entrar_circulo', kwargs={'circulo_id': self.pk, })

    def __unicode__(self):
        return u'%s %s' % (self.get_tipo_display(), self.titulo)

class CirculoMembro(models.Model):
    class Meta:
        verbose_name = u'Colaborador do Círculo/GT'
        verbose_name_plural = u'Colaboradores do Círculo/GT'

    circulo = models.ForeignKey(Circulo)
    membro = models.ForeignKey(Membro)
    administrador = models.BooleanField(default=False)
    grupousuario = models.ForeignKey(GrupoUsuario, editable=False, blank=True, null=True)
#    tipo_alerta = models.CharField(u'Recebimento de Notificações') # Frequência de recebimento de alertas
#    representante = models.ForeignKey(Membro) # Membro que representa alguém no Círculo

# Só mostrar o campo Oficial se o usuário for do grupo Diretoria
# Só permitir a edição do evento se o membro for administrador do círculo
    def __unicode__(self):
        return u'#%s' % self.pk
@receiver(signals.pre_save, sender=CirculoMembro)
def cria_grupousuario_circulomemebro_signal(sender, instance, raw, using, *args, **kwargs):
    if instance.circulo.grupo and instance.membro.usuario and not instance.grupousuario:
        instance.grupousuario = GrupoUsuario.objects.create(grupo=instance.circulo.grupo, usuario=instance.membro.usuario)
@receiver(signals.post_delete, sender=CirculoMembro)
def remove_grupousuario_circulomemebro_signal(sender, instance, using, *args, **kwargs):
    if instance.grupousuario:
        instance.grupousuario.delete()


# Eventos que devem ser divulgados no site
class CirculoEvento(models.Model):
    circulo = models.ForeignKey(Circulo)
    nome = models.CharField(u'Título', max_length=100)
    dt_evento = models.DateTimeField(u'Dt.Evento')
    local = models.TextField(u'Local do Evento')
    privado = models.BooleanField(u'Privado', default=True)

    def __unicode__(self):
        return u'%s' % self.nome

    class Meta:
        verbose_name = u'Evento do Círculo'
        verbose_name_plural = u'Eventos dos círculos'


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


class Campanha(models.Model):
    class Meta:
        ordering = ('dtenvio', )

    lista = models.ForeignKey(Lista, null=True, on_delete=models.SET_NULL)
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

    def send_email_test(self, to):
        send_email_thread(subject=self.assunto, to=to, template=self.template)

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
            user = User.objects.get_or_create(username="sys")[0]
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
                    Campanha.objects.filter(pk=campanha_id).update(qtde_erros=len(emails_list))
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
                    try:
                        msg.send()
                        LogEntry.objects.log_action(
                            user_id = user_id,
                            content_type_id = campanha_ct.pk,
                            object_id = campanha.pk,
                            object_repr = u"%s" % campanha,
                            action_flag = CHANGE,
                            change_message = u'[INFO] Emails enviados com sucesso para: %s.' % u", ".join(emails)
                        )
                        # Atualiza o número de envios
                        Campanha.objects.filter(pk=campanha_id).update(qtde_envio=F('qtde_envio')+len(emails))
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
                    Campanha.objects.filter(pk=campanha_id).update(qtde_erros=campanha.lista.listacadastro_set.filter(pessoa__status_email__in=('A', 'N', )).count()-F('qtde_envio'))
                    return

            LogEntry.objects.log_action(
                user_id = user_id,
                content_type_id = campanha_ct.pk,
                object_id = campanha.pk,
                object_repr = u"%s" % campanha,
                action_flag = CHANGE,
                change_message = u'[INFO] Envio Finalizado'
            )


        emails_list = self.lista.listacadastro_set.filter(pessoa__status_email__in=('A', 'N', )).values_list('pessoa__email', flat=True).order_by('pessoa__email')
        if resumir == True:
            emails_list = emails_list[self.qtde_envio:]
            self.qtde_erros = 0
        self.dtenvio = datetime.now()
        self.save()

        th=Thread(target=_send_campanha_thread, kwargs={'campanha_id': self.pk, 'user_id': user.pk,  'emails_list': emails_list, })
        th.start()

    def __unicode__(self):
        return self.assunto
