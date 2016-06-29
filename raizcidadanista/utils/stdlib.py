# -*- coding: utf-8 -*-
from datetime import date

def normalizar_data(data_string):
    if '/' in data_string:
        dia, mes, ano = data_string.split('/')
    else:
        ano, mes, dia = data_string.split('-')
    if len(ano) == 2:
        ano = '20%s' % ano
    return date(day=int(dia), month=int(mes), year=int(ano))