# -*- coding: utf-8 -*-
from django.core.files.storage import FileSystemStorage
from django.utils.text import get_valid_filename
from django.template.defaultfilters import slugify
from django.conf import settings

import os, uuid


class SpecialCharFileSystemStorage(FileSystemStorage):
    """
    Remove Special Char filesystem storage
    """

    def get_valid_name(self, name):
        nome, extensao = os.path.splitext(name)
        return os.path.join(slugify(get_valid_filename(nome)) + extensao.lower())


class UuidFileSystemStorage(FileSystemStorage):

    def get_valid_name(self, name):
        nome, extensao = os.path.splitext(name)
        return os.path.join(str(uuid.uuid4()) + extensao.lower())


def save_file(file, path=''):
    if path and not os.path.isdir(os.path.join(settings.MEDIA_ROOT, path)):
        os.makedirs(os.path.join(settings.MEDIA_ROOT, path))

    nome, extensao = os.path.splitext(file._get_name())
    filename = os.path.join(str(uuid.uuid4()) + extensao.lower())
    with open(os.path.join(settings.MEDIA_ROOT, path, filename), 'wb') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return os.path.join(settings.MEDIA_URL, path, filename)