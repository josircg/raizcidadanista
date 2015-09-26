# coding:utf-8
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from poweradmin.admin import PowerModelAdmin

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