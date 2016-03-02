# BruteBuster by Cyber Security Consulting (www.csc.bg)

"""Admin settings for the BruteBuster module"""

from django.contrib import admin
from BruteBuster.models import FailedAttempt, FailedURLAttempt


class AdminFailedAttempt(admin.ModelAdmin):
    list_display = ('username', 'IP', 'failures', 'timestamp', 'blocked')
    search_fields = ('username', 'IP', )
admin.site.register(FailedAttempt, AdminFailedAttempt)


class AdminFailedURLAttempt(admin.ModelAdmin):
    list_display = ('IP', 'failures', 'timestamp', 'blocked')
    search_fields = ('IP', )
admin.site.register(FailedURLAttempt, AdminFailedURLAttempt)
