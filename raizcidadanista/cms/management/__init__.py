# coding:utf-8
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission, User

def create_views_permissions():
    #resumofaturamento
    Permission.objects.get_or_create(
        name='Can view resumofaturamento',
        codename='view_resumofaturamento',
        content_type=ContentType.objects.get_for_model(User)
    )
    #Caixa
    Permission.objects.get_or_create(
        name='Can view caixa',
        codename='view_caixa',
        content_type=ContentType.objects.get_for_model(User)
    )

    #Caixa - Centro de Custos
    Permission.objects.get_or_create(
        name='Can view caixa - centro de custos',
        codename='view_contacaixa',
        content_type=ContentType.objects.get_for_model(User)
    )

    #import_pagseguro
    Permission.objects.get_or_create(
        name='Can view import PagSeguro',
        codename='import_pagseguro',
        content_type=ContentType.objects.get_for_model(User)
    )

    #import rps
    Permission.objects.get_or_create(
        name='Can view import RPS',
        codename='import_rps',
        content_type=ContentType.objects.get_for_model(User)
    )


create_views_permissions()