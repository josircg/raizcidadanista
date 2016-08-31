# coding:utf-8
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.conf.urls.defaults import patterns, url
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.shortcuts import get_object_or_404
from django.contrib.auth import login, logout

from poweradmin.admin import PowerModelAdmin, PowerButton

#Registrar as preferências do django admin tools
from admin_tools.dashboard.models import DashboardPreferences


class DashboardPreferencesAdmin(PowerModelAdmin):
    list_display = ('user', )
    list_filter = ('user', )

    def reset_dashboard(self, request):
        DashboardPreferences.objects.filter(user=request.user).delete()
        DashboardPreferences(
            user = request.user,
            data = '{}',
        ).save()
        return HttpResponseRedirect(reverse('admin:index'))

    def get_urls(self):
        from django.conf.urls.defaults import patterns, url
        urls_originais = super(DashboardPreferencesAdmin, self).get_urls()
        urls_customizadas = patterns('',
            url(r'^reset-dashboard/$', self.wrap(self.reset_dashboard), name='reset_dashboard'),
        )
        return urls_customizadas + urls_originais

admin.site.register(DashboardPreferences, DashboardPreferencesAdmin)


def user_unicode(obj):
    return u'%s (%s)' % (obj.get_full_name(), obj.username, )
User.__unicode__ = user_unicode
def user_first_name(obj):
    if obj.membro.exists() and obj.membro.latest('pk').apelido:
        return obj.membro.latest('pk').apelido
    if obj.first_name:
        return obj.first_name
    return obj.username
User.get_first_name = user_first_name
admin.site.unregister(User)
class CustomUserAdmin(UserAdmin, PowerModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff' )
    list_filter = ('is_active', 'is_staff', 'groups',)
    readonly_fields = ('last_login', 'date_joined',)
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions', )

    def personificar(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        logout(request)
        user.backend='django.contrib.auth.backends.ModelBackend'
        login(request, user)
        messages.info(request, u'Você está logado agora como %s!' % user)
        return HttpResponseRedirect(reverse('admin:index'))

    def get_urls(self):
        urls_originais = super(CustomUserAdmin, self).get_urls()
        urls_customizadas = patterns('',
            url(r'^personificar/(?P<user_id>.*)/$', self.wrap(self.personificar), name='auth_user_personificar'),
        )
        return urls_customizadas + urls_originais

    def get_buttons(self, request, object_id):
        buttons = super(CustomUserAdmin, self).get_buttons(request, object_id)
        if object_id:
            obj = self.get_object(request, object_id)
            if obj and obj.is_active:
                buttons.append(PowerButton(url=reverse('admin:auth_user_personificar', kwargs={'user_id': object_id, }), label=u'Personificar'))
        return buttons
admin.site.register(User, CustomUserAdmin)