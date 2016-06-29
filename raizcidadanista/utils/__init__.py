# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse


def url_display(obj):
    content_type = ContentType.objects.get_for_model(obj)
    try:
        return u'<a href="%s">%s</a>' % (
            reverse('admin:%s_%s_change' % (content_type.app_label, content_type.model), args=(obj.pk, )),
            obj,
        )
    except:
        return u'%s' % obj