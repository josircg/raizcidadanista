# coding: utf-8
from django.conf.urls import patterns, include, url
from views import *
from forms import CustomPasswordResetForm
from cms.sitemap import sitemaps

urlpatterns = patterns('',
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^pesquisa/$', SearchView.as_view(), name='search'),
    url(r'^circulos/$', CirculosView.as_view(), name='circulos'),
    url(r'^mapa/$', MapaView.as_view(), name='mapa'),
    url(r'^gts/$', GTsView.as_view(), name='gts'),
    url(r'^circulos-tematicos/$', CirculosTematicos.as_view(), name='gts'),
    url(r'^contato/$', ContatoView.as_view(), name='contato'),
    url(r'^section/(?P<slug>[-_\w]+)/$', SectionDetailView.as_view(), name='section'),
    url(r'^download/(?P<file_uuid>[-_\w]+)/$', FileDownloadView.as_view(), name='download'),
    url(r'^link/a/(?P<article_slug>[-_\w]+)/$', LinkConversionView.as_view(), name='link'),
    url(r'^link/s/(?P<section_slug>[-_\w]+)/$', LinkConversionView.as_view(), name='link'),
    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}, name="sitemap"),
    url(r'^robots\.txt$', RobotsView.as_view(), name="robots"),

    url(r'^login/$', 'django.contrib.auth.views.login', kwargs={'template_name': 'auth/login.html',}, name='cms_login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', kwargs={'template_name': 'auth/logout.html',}, name='cms_logout'),
    url(r'^password_change/$', 'django.contrib.auth.views.password_change', kwargs={'template_name': 'auth/password_change_form.html'}, name='cms_password_change'),
    url(r'^password_change/done/$', 'django.contrib.auth.views.password_change_done', kwargs={'template_name': 'auth/password_change_done.html',}, name='cms_password_change_done'),
    url(r'^password_reset/$', 'django.contrib.auth.views.password_reset', kwargs={
        'template_name': 'auth/password_reset_form.html',
        'email_template_name': 'auth/password_reset_email.html',
        'password_reset_form': CustomPasswordResetForm,
    }, name='cms_password_reset'),
    url(r'^password_reset/done/$', 'django.contrib.auth.views.password_reset_done', kwargs={'template_name': 'auth/password_reset_done.html',}, name='cms_password_reset_done'),
    url(r'^reset/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        'django.contrib.auth.views.password_reset_confirm',
        kwargs={'template_name': 'auth/password_reset_confirm.html',},
        name='cms_password_reset_confirm'),
    url(r'^reset/done/$', 'django.contrib.auth.views.password_reset_complete', kwargs={'template_name': 'auth/password_reset_complete.html',}, name='cms_password_reset_complete'),

    url(r'^(?P<slug>[-_\w]+)/?$', ArticleDetailView.as_view(), name='article'),
)
