# coding:utf-8
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission, User

def create_views_permissions():
    Permission.objects.get_or_create(
        name='Can view Caixa',
        codename='view_caixa',
        content_type=ContentType.objects.get_for_model(User)
    )
create_views_permissions()