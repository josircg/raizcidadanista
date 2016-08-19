# coding: utf-8
from django.db import models
from django.contrib.auth.models import User


class UserAdminConfig(models.Model):
    user = models.ForeignKey(User)
    url_name = models.CharField(max_length=100)  # identify the config
    url_full_path = models.TextField()