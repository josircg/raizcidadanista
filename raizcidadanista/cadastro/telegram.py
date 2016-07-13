# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse

import telepot


class BotRaiz(object):
    TELEGRAM_API_TOKEN = '222913462:AAF7jAFEDDMcuBnddUltEJkDOmTCmqQ_AfY'

    def __init__(self, *args, **kwargs):
        super(BotRaiz, self).__init__(*args, **kwargs)
        self.bot = telepot.Bot(self.TELEGRAM_API_TOKEN)
        self.bot.setWebhook()

    def listen(self):
        def handle(msg):
            telegram_id = msg['from']['id']
            if msg['text'] == '/start':
                link = u'%s%s?telegram_id=%s' % (settings.SITE_HOST, reverse('telegram'), telegram_id)
                self.bot.sendMessage(telegram_id, u'Oi. Clique no link abaixo para associar o seu Telegram ao seu usuário do Raiz e receber as atulizações do fórum aqui mesmo. %s' % link)

        self.bot.message_loop(handle)

    def sendMessage(self, telegram_id, msg):
        self.bot.sendMessage(telegram_id, msg)


# Iniciar o bot
bot = BotRaiz()
bot.listen()