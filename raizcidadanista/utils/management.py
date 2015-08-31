# coding:utf-8
from django.contrib.contenttypes.models import ContentType
from django.db.models import signals
from django.utils.encoding import smart_unicode
from django.conf import settings

def update_contenttypes(app, **kwargs):
    #No post_syncdb o app é um object, já no post_migrate é uma string
    if not isinstance(app, str):
        app = app.__name__.split('.')[-2]

    for ct in ContentType.objects.filter(app_label=app):
        try:
            name = smart_unicode(ct.model_class()._meta.verbose_name_raw)
            if ct.name != name:
                print "Updating ContentType's name: '%s' -> '%s'" % (ct.name, name)
                ct.name=name
                ct.save()
        except: pass

# Se tiver a aplicação south no INSTALLED_APPS,
# ele conecta o update_contenttypes ao post_migrate
if 'south' in settings.INSTALLED_APPS:
    from south.signals import post_migrate
    post_migrate.connect(update_contenttypes)

signals.post_syncdb.connect(update_contenttypes)