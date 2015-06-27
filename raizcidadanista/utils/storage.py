# -*- coding: utf-8 -*-
from django.core.files.storage import FileSystemStorage
from django.utils.text import get_valid_filename
from django.template.defaultfilters import slugify


class SpecialCharFileSystemStorage(FileSystemStorage):
    """
    Remove Special Char filesystem storage
    """
    
    def get_valid_name(self, name):
        return u"%s.%s" % (slugify(get_valid_filename("".join(name.split('.')[:-1]))), name.split('.')[-1])