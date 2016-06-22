# coding: utf-8
from django.views.generic import DetailView, TemplateView, View, FormView, RedirectView
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404, HttpResponsePermanentRedirect, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.contrib import messages
from django.conf import settings
from django.db.models import Q

from BruteBuster.models import FailedAttempt, BB_MAX_FAILURES, BB_BLOCK_INTERVAL

from municipios.models import UF
from cadastro.models import Circulo, Membro, CirculoMembro
from financeiro.models import MetaArrecadacao

from models import Article, Section, URLMigrate, FileDownload, Recurso, Permissao, \
    GroupType
from forms import ArticleCommentForm, ContatoForm

from twython import Twython
import mimetypes, os, cgi, urllib, facebook

from datetime import datetime, date


class CirculosView(TemplateView):
    template_name = 'circulos.html'

    def get_context_data(self, **kwargs):
        context = super(CirculosView, self).get_context_data(**kwargs)
        context['estados'] = UF.objects.all().order_by('nome')
        return context


class MapaView(TemplateView):
    template_name = 'mapa.html'

    def get_context_data(self, **kwargs):
        context = super(MapaView, self).get_context_data(**kwargs)
        colaboradores = {}
        for estado in UF.objects.all().order_by('nome'):
            colaboradores[estado.nome] = Membro.objects.filter(uf=estado).count()
        context['colaboradores'] = colaboradores
        context['estados'] = UF.objects.all().order_by('nome')
        return context


class GTsView(TemplateView):
    template_name = 'gts.html'

    def get_context_data(self, **kwargs):
        context = super(GTsView, self).get_context_data(**kwargs)
        context['gts'] = Circulo.objects.filter(tipo='G', oficial=True).order_by('titulo')
        return context


class CirculosTematicos(TemplateView):
    template_name = 'circulos-tematicos.html'

    def get_context_data(self, **kwargs):
        context = super(CirculosTematicos, self).get_context_data(**kwargs)
        context['circulos'] = Circulo.objects.filter(tipo__in=('T', 'I'), oficial=True).order_by('titulo')
        return context


class MetaView(DetailView):
    model = MetaArrecadacao
    template_name = 'meta.html'


class MetaDepositosView(DetailView):
    model = MetaArrecadacao
    template_name = 'meta-depositos.html'

    def get_context_data(self, **kwargs):
        context = super(MetaDepositosView, self).get_context_data(**kwargs)
        receitas = self.object.receitas()
        if self.request.GET.get('data-inicial'):
            try:
                data_inicial = datetime.strptime(self.request.GET.get('data-inicial'), '%d/%m/%Y').date()
                receitas = receitas.filter(dtpgto__gte=data_inicial)
                context['data_inicial'] = data_inicial
            except: pass
            try:
                data_final = datetime.strptime(self.request.GET.get('data-final'), '%d/%m/%Y').date()
                receitas = receitas.filter(dtpgto__lte=data_final)
                context['data_final'] = data_final
            except: pass
        context['receitas'] = receitas
        return context


class ContatoView(FormView):
    template_name = 'contato.html'
    template_success_name = 'contato.html'
    form_class = ContatoForm

    def form_valid(self, form):
        if self.request.GET.get('adm'):
            try:
                adm = CirculoMembro.objects.get(pk=self.request.GET.get('adm'))
                form.sendemail(to=[adm.membro.email, ], bcc=['correio@raiz.org.br', ])
            except CirculoMembro.DoesNotExist:
                form.sendemail()
        messages.info(self.request, u"Mensagem enviada com sucesso!")
        return self.response_class(
            request=self.request,
            template=self.template_success_name,
            context={
                'form': self.form_class(),
            }
        )

    def form_invalid(self, form):
        messages.error(self.request, u"Preencha corretamente todos os dados!")
        return super(ContatoView, self).form_invalid(form)


class ArticleDetailView(DetailView):
    model = Article
    form = ArticleCommentForm

    def get_template_names(self):
        templates = []
        for section in self.object.sections.all():
            templates.append('%s/article.html' % section.slug)
            templates.append('%s/%s.html' % (section.slug, self.object.slug,))
        templates.append('article/%s.html' % self.object.slug)
        templates.append('article.html')
        return templates

    def get_context_data(self, **kwargs):
        form = self.form()
        if self.request.method == 'POST':
            form = self.form(self.request.POST, initial={'article': self.object, })
            if form.is_valid() and self.object.allow_comments in ('A', 'P'):
                form.instance.article = self.object
                form.save()
                form.sendemail()
                form = self.form()
                messages.info(self.request, u'Comentário enviado!')
            else:
                messages.error(self.request, u'Corrija os erros abaixo!')
        return {
            'article': self.object,
            'form': form,
        }

    def post(self, *args, **kwargs):
        return self.get(*args, **kwargs)

    def get(self, *args, **kwargs):
        try:
            response = super(ArticleDetailView, self).get(*args, **kwargs)
            # Redirecionar para a home se: A sessão tem permissão e o usuário não está nesse grupo
            if not self.object.have_perm(self.request.user):
                messages.error(self.request, u'Você não tem permissão para acessar esse artigo!')
                return HttpResponseRedirect(reverse('home'))
            self.object.views += 1
            self.object.save()
            return response
        except Http404:
            return URLMigrateView().get(self.request, old_url=self.request.path_info)


class SectionDetailView(DetailView):
    model = Section

    def get_template_names(self):
        if self.object.template:
            return [self.object.template, ]
        return [
            'section/%s.html' % self.object.slug,
            '%s/section.html' % self.object.slug,
            'section.html',
        ]

    def get_context_data(self, **kwargs):
        articles_list = []
        articles_queryset = self.object.get_articles()

        # Na setion 'eventos' mostrar apenas os articles com data >= hoje
        if self.object.slug == 'eventos':
            if self.request.GET.get('all'):
                articles_queryset = articles_queryset.filter(created_at__lt=date.today()).order_by('-created_at')
            else:
                articles_queryset = articles_queryset.filter(created_at__gte=date.today()).order_by('created_at')
        for article in articles_queryset:
            if article.have_perm(self.request.user):
                articles_list.append(article)

        paginator = Paginator(articles_list, 10)

        page = self.request.GET.get('page')
        try:
            articles = paginator.page(page)
        except PageNotAnInteger:
            articles = paginator.page(1)
        except EmptyPage:
            articles = paginator.page(paginator.num_pages)
        return {
            'section': self.object,
            'articles': articles,
        }


    def get(self, *args, **kwargs):
        response = super(SectionDetailView, self).get(*args, **kwargs)
        # Redirecionar para a home se: A sessão tem permissão e o usuário não está nesse grupo
        if not self.object.have_perm(self.request.user):
            messages.error(self.request, u'Você não tem permissão para acessar essa sessão!')
            return HttpResponseRedirect(reverse('home'))
        self.object.views += 1
        self.object.save()
        return response


class HomeView(TemplateView):
    template_name = 'home.html'


class LinkConversionView(View):
    def get(self, request, *args, **kwargs):
        if not 'next' in request.GET:
            raise Http404

        if 'section_slug' in kwargs:
            section = get_object_or_404(Section, slug=kwargs.get('section_slug'))
            section.conversions += 1
            section.save()
        elif 'article_slug' in kwargs:
            article = get_object_or_404(Article, slug=kwargs.get('article_slug'))
            article.conversions += 1
            article.save()

        next = request.GET.get('next')
        if not 'http' in next:
            next = 'http://%s' % next
        return redirect(next)


class URLMigrateView(View):
    def get(self, request, old_url, *args, **kwargs):
        url = get_object_or_404(URLMigrate, old_url=old_url)
        url.views += 1
        url.save()
        if url.redirect_type == 'M':
            return HttpResponsePermanentRedirect(url.new_url)
        return HttpResponseRedirect(url.new_url)


class FileDownloadView(View):
    def get(self, request, file_uuid, *args, **kwargs):
        file_download = get_object_or_404(FileDownload, uuid=file_uuid)
        if file_download.is_expired():
            raise Http404()

        file_download.count += 1
        file_download.save()

        mimetype = mimetypes.guess_type(file_download.file.path)[0]
        return HttpResponse(file_download.file.read(), content_type=mimetype)


class SearchView(TemplateView):
    template_name = 'search.html'

    def get_context_data(self, **kwargs):
        q = self.request.GET.get('q')
        results_list = []
        if q:
            articles_list = Article.objects.filter(
                is_active=True
            ).filter(
                Q(title__icontains=q) |
                Q(header__icontains=q) |
                Q(content__icontains=q) |
                Q(keywords__icontains=q)
            ).distinct()
            for article in articles_list:
                if article.have_perm(self.request.user):
                    results_list.append({
                        'title': article.title,
                        'object': article,
                    })
            results_list = sorted(results_list, key=lambda k: k['title'])

        paginator = Paginator(results_list, 10)
        page = self.request.GET.get('page')
        try:
            results = paginator.page(page)
        except PageNotAnInteger:
            results = paginator.page(1)
        except EmptyPage:
            results = paginator.page(paginator.num_pages)
        return {
            'q': q,
            'results': results,
        }


class RobotsView(View):
    def get(self, request, *args, **kwargs):
        robots = Recurso.objects.get_or_create(recurso='ROBOTS')[0]
        if robots.ativo:
            return HttpResponse(u'User-agent: *\nAllow: *\nSitemap: %s%s' % (settings.SITE_HOST, reverse('sitemap')), content_type='text/plain')
        return HttpResponse(u'User-agent: *\nDisallow: *', content_type='text/plain')


class LoginView(FormView):
    template_name = 'auth/login.html'
    form_class = AuthenticationForm

    def form_valid(self, form):
        login(self.request, form.get_user())
        if self.request.session.test_cookie_worked():
            self.request.session.delete_test_cookie()

        if self.request.GET.get('next'):
            messages.info(self.request, u'Você foi autenticado com sucesso.')
            return HttpResponseRedirect(self.request.GET.get('next'))
        messages.info(self.request, u'Você foi autenticado com sucesso. Para acessar o ambiente administrativo, <a href="%s">clique aqui</a>.' % reverse('admin:index'))
        return HttpResponseRedirect(reverse('forum'))

    def form_invalid(self, form):
        error_message = u"Preencha corretamente todos os dados!"
        try:
            IP_ADDR = self.request.META.get('REMOTE_ADDR', None)
            failed = FailedAttempt.objects.filter(username=form.data.get('username'), IP=IP_ADDR).latest('timestamp')
            if failed.blocked():
                error_message = u"Você está bloqueado porque errou sua senha mais de %s vezes. Aguarde %s minutos e tente novamente!" % (BB_MAX_FAILURES, BB_BLOCK_INTERVAL, )
        except FailedAttempt.DoesNotExist: pass
        messages.error(self.request, error_message)
        return super(LoginView, self).form_invalid(form)



class LoginFacebookView(RedirectView):
    def get(self, request, *args, **kwargs):
        faceargs = {
            'client_id': settings.FACEBOOK_APP_ID,
            'redirect_uri': request.build_absolute_uri(),
            'scope': ' '.join(settings.FACEBOOK_APP_PERM)
        }
        if not request.GET.get("code"):
            return HttpResponseRedirect("https://graph.facebook.com/oauth/authorize?%s" % urllib.urlencode(faceargs))
        else:
            try:
                faceargs["client_secret"] = settings.FACEBOOK_APP_SECRET_KEY
                faceargs["code"] = request.GET.get("code")

                response = cgi.parse_qs(urllib.urlopen(
                    "https://graph.facebook.com/oauth/access_token?" +
                    urllib.urlencode(faceargs)).read())
                access_token = response["access_token"][-1]

                graph = facebook.GraphAPI(access_token)
                user_data = graph.get_object("me", fields="id,name,email")

                membro = None
                if Membro.objects.filter(facebook_id=user_data.get('id')).exists():
                    membro = Membro.objects.filter(facebook_id=user_data.get('id')).latest('pk')
                    # Atualiza o Membro
                    membro.facebook_access_token = access_token
                    membro.save()
                elif Membro.objects.filter(email=user_data.get('email')).exists():
                    membro = Membro.objects.filter(email=user_data.get('email')).latest('pk')
                    # Atualiza o Membro
                    membro.facebook_id = user_data.get('id')
                    membro.facebook_access_token = access_token
                    membro.save()

                elif Membro.objects.filter(nome=user_data.get('name')).exists():
                    membro = Membro.objects.filter(nome=user_data.get('name')).latest('pk')
                    # Atualiza o Membro
                    membro.facebook_id = user_data.get('id')
                    membro.facebook_access_token = access_token
                    membro.save()

                if membro and membro.usuario:
                    # Realiza o login
                    membro.usuario.backend='django.contrib.auth.backends.ModelBackend'
                    login(request, membro.usuario)
                    messages.info(request, u'Você foi autenticado com sucesso. Para acessar o ambiente administrativo, <a href="%s">clique aqui</a>.' % reverse('admin:index'))
                    return HttpResponseRedirect('/')
                else:
                    messages.info(request, u'Colaborador/Filiado não encontrado. Provavelmente o seu email está diferente do que você utlizou para se registrar no site ou então você ainda não é nosso colaborador.')
            except:
                messages.info(request, u'É preciso autorizar o Facebook.')
            return HttpResponseRedirect(reverse('cms_login'))


class LoginTwitterView(RedirectView):
    def get(self, request, *args, **kwargs):
        if not request.GET.get("oauth_token"):
            twitter = Twython(settings.TWITTER_KEY, settings.TWITTER_SECRET)

            # Request an authorization url to send the user to...
            callback_url = request.build_absolute_uri(reverse('cms_login_twitter'))
            auth_props = twitter.get_authentication_tokens(callback_url)

            # Then send them over there, durh.
            request.session['request_token'] = auth_props
            return HttpResponseRedirect(auth_props['auth_url'])
        else:
            try:
                oauth_token = request.session['request_token']['oauth_token']
                oauth_token_secret = request.session['request_token']['oauth_token_secret']
                twitter = Twython(settings.TWITTER_KEY, settings.TWITTER_SECRET, oauth_token, oauth_token_secret)
                # Retrieve the tokens we want...
                authorized_tokens = twitter.get_authorized_tokens(request.GET['oauth_verifier'])

                twitter = Twython(settings.TWITTER_KEY, settings.TWITTER_SECRET, authorized_tokens['oauth_token'], authorized_tokens['oauth_token_secret'])
                user_data = twitter.verify_credentials()

                membro = None
                if Membro.objects.filter(twitter_id=authorized_tokens.get('user_id')).exists():
                    membro = Membro.objects.filter(twitter_id=authorized_tokens.get('user_id')).latest('pk')
                    # Atualiza o Membro
                    membro.twitter_oauth_token = authorized_tokens.get('oauth_token')
                    membro.twitter_oauth_token_secret = authorized_tokens.get('oauth_token_secret')
                    membro.save()
                elif Membro.objects.filter(nome=user_data.get('name')).exists():
                    membro = Membro.objects.filter(nome=user_data.get('name')).latest('pk')
                    # Atualiza o Membro
                    membro.twitter_id = authorized_tokens.get('user_id')
                    membro.twitter_oauth_token = authorized_tokens.get('oauth_token')
                    membro.twitter_oauth_token_secret = authorized_tokens.get('oauth_token_secret')
                    membro.save()

                if membro and membro.usuario:
                    # Realiza o login
                    membro.usuario.backend='django.contrib.auth.backends.ModelBackend'
                    login(request, membro.usuario)
                    messages.info(request, u'Você foi autenticado com sucesso. Para acessar o ambiente administrativo, <a href="%s">clique aqui</a>.' % reverse('admin:index'))
                    return HttpResponseRedirect('/')
                else:
                    messages.info(request, u'Colaborador/Filiado não encontrado. Provavelmente o seu nome está diferente do que você utlizou para se registrar no site ou então você ainda não é nosso colaborador.')
            except:
                messages.info(request, u'É preciso autorizar o Twitter.')
            return HttpResponseRedirect(reverse('cms_login'))