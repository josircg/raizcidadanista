# -*- coding: utf-8 -*-
from django.core.management.base import NoArgsCommand

from cadastro.telegram import bot
from time import sleep


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        bot.listen()

        while True:
            sleep(10)