# -*- coding: utf-8 -*-
from datetime import date

# simula a função clássica do Oracle: Retorna uma alternativa caso o objeto esteja vazio
def nvl(objeto,alternativa):
    if objeto == None:
        return alternativa
    else:
        return objeto

# Retorna a string capitalizada, considerando preposições em Português
def upper_first(value):
    result = ''
    for sentence in value.split(" "):
        if sentence in ['de','da','do','para','e','entre']:
            result = result + " " + sentence
        else:
            result = result + " " + capfirst(sentence)
    return result.lstrip()

def normalizar_data(data_string):
    if '/' in data_string:
        dia, mes, ano = data_string.split('/')
    else:
        ano, mes, dia = data_string.split('-')
    if len(ano) == 2:
        ano = '20%s' % ano
    return date(day=int(dia), month=int(mes), year=int(ano))
