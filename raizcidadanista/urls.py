from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.conf import settings

from filebrowser.sites import site
from cms.forms import CustomPasswordResetForm
from cms.views import URLMigrateView
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/password_reset/$', 'django.contrib.auth.views.password_reset', {'post_reset_redirect': '/admin/password_reset/done/', 'password_reset_form': CustomPasswordResetForm}, name='admin_password_reset'),
    url(r'^admin/password_reset/done/$', 'django.contrib.auth.views.password_reset_done', name="admin_password_reset_done"),
    url(r'^admin/reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm', {'post_reset_redirect': '/admin/reset/done/'}, name="admin_password_reset_confirm"),
    url(r'^admin/reset/done/$', 'django.contrib.auth.views.password_reset_complete', name="admin_password_reset_complete"),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/filebrowser/', include(site.urls)),
    url(r'^admin_tools/', include('admin_tools.urls')),
    url(r'^municipios/', include('municipios.urls')),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/site/icon/favicon.ico')),
    url(r'^forum/', include('forum.urls')),
    url(r'^', include('cadastro.urls')),
    #CMS
    url(r'^', include('cms.urls')),
    url(r'^ckeditor/', include('ckeditor.urls')),
    url(r'^chaining/', include('smart_selects.urls')),
)

if 'theme' in settings.INSTALLED_APPS:
    urlpatterns += patterns('', url(r'^', include('theme.urls')))

if settings.LOCAL:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


#Migrate URLs
urlpatterns += patterns('',
    url(r'^(.*)$', URLMigrateView.as_view(), name='cms_url_migrate'),
)