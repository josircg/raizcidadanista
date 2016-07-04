#-*- coding: utf-8 -*-
from django.core.management.base import NoArgsCommand

from cms.models import Recurso


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        Recurso.get_cloudtags()