# coding:utf-8

from django.contrib import admin

from models import *
from views import *

class CirculoMembroInline(admin.TabularInline):
    model = CirculoMembro
    extra = 0
    verbose_name = u'Círculo do Membro'
    verbose_name_plural = u'Círculos do Membro'

class MembroAdmin(admin.ModelAdmin):
    inline = (CirculoMembroInline,)

admin.site.register(Circulo)
admin.site.register(Membro, MembroAdmin)
