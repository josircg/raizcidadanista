# -*- coding:utf-8 -*-
from django.contrib import admin

from models import *
from views import *


class CirculoMembroInline(admin.TabularInline):
    model = CirculoMembro
    extra = 0

class MembroAdmin(admin.ModelAdmin):
    inline = (CirculoMembroInline,)
admin.site.register(Membro, MembroAdmin)


admin.site.register(Pessoa)
admin.site.register(Circulo)