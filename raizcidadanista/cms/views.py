# coding: utf-8
from django.views.generic import DetailView, TemplateView, View, FormView
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404, HttpResponsePermanentRedirect, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.contrib import messages
from django.conf import settings
from django.db.models import Q

from municipios.models import UF
from cadastro.models import Circulo

from models import Article, Section, URLMigrate, FileDownload, Recurso, Permissao, \
    GroupType
from forms import ArticleCommentForm, CMSUserCreationForm

import mimetypes, os


class CirculosView(TemplateView):
    template_name = 'circulos.html'

    def get_context_data(self, **kwargs):
        context = super(CirculosView, self).get_context_data(**kwargs)
        circulos = []
        for uf in UF.objects.all().order_by('nome'):
            queryset = Circulo.objects.filter(uf=uf)
            if queryset:
                cidades = []
                for query in queryset:
                    if query.site_externo:
                        cidades.append(u'<a href="%s" target="_blank">%s</a>' % (query.site_externo, query.municipio, ))
                    else:
                        cidades.append(query.municipio)
                circulos.append((uf.nome, u"Cidades: %s" % (u", ".join(cidades))))
            else:
                circulos.append((uf.nome, u"Ainda não existe nenhum círculo em seu estado."))
        context['circulos'] = circulos
        return context

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
        response = super(ArticleDetailView, self).get(*args, **kwargs)
        # Redirecionar para a home se: A sessão tem permissão e o usuário não está nesse grupo
        if not self.object.have_perm(self.request.user):
            messages.error(self.request, u'Você não tem permissão para acessar esse artigo!')
            return HttpResponseRedirect(reverse('home'))
        self.object.views += 1
        self.object.save()
        return response


class SectionDetailView(DetailView):
    model = Section

    def get_template_names(self):
        return [
            'section/%s.html' % self.object.slug,
            '%s/section.html' % self.object.slug,
            'section.html',
        ]

    def get_context_data(self, **kwargs):
        articles_list = self.object.get_articles()
        paginator = Paginator(articles_list, 5)

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
                results_list.append({
                    'title': article.title,
                    'object': article,
                })
            results_list = sorted(results_list, key=lambda k: k['title'])

        paginator = Paginator(results_list, 5)
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
            return HttpResponse(u'User-agent: *\nAllow: *', content_type='text/plain')
        return HttpResponse(u'User-agent: *\nDisallow: *', content_type='text/plain')


class SignupView(FormView):
    form_class = CMSUserCreationForm
    template_name = 'auth/signup.html'
    template_name_done = 'auth/signup_done.html'

    def form_valid(self, form):
        form.save()
        form = self.form_class()
        return self.response_class(
            request=self.request,
            template=self.template_name_done,
            context=self.get_context_data(form=form),
        )