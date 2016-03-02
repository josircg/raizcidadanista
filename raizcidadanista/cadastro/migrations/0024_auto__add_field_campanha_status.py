# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Campanha.status'
        db.add_column('cadastro_campanha', 'status',
                      self.gf('django.db.models.fields.CharField')(default='E', max_length=1),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Campanha.status'
        db.delete_column('cadastro_campanha', 'status')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'cadastro.campanha': {
            'Meta': {'ordering': "('dtenvio',)", 'object_name': 'Campanha'},
            'assunto': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'dtenvio': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lista': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cadastro.Lista']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'qtde_envio': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'qtde_erros': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'qtde_views': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'E'", 'max_length': '1'}),
            'template': ('django.db.models.fields.TextField', [], {})
        },
        'cadastro.circulo': {
            'Meta': {'ordering': "('tipo', 'titulo')", 'object_name': 'Circulo'},
            'descricao': ('django.db.models.fields.TextField', [], {}),
            'dtcadastro': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now'}),
            'grupo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Grupo']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'imagem': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'municipio': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'oficial': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'permitecadastro': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'site_externo': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'A'", 'max_length': '1'}),
            'tipo': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'titulo': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'uf': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['municipios.UF']", 'null': 'True', 'blank': 'True'})
        },
        'cadastro.circuloevento': {
            'Meta': {'object_name': 'CirculoEvento'},
            'artigo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Article']", 'null': 'True', 'blank': 'True'}),
            'circulo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cadastro.Circulo']"}),
            'dt_evento': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'local': ('django.db.models.fields.TextField', [], {}),
            'nome': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'privado': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'cadastro.circulomembro': {
            'Meta': {'unique_together': "(('circulo', 'membro'),)", 'object_name': 'CirculoMembro'},
            'administrador': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'circulo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cadastro.Circulo']"}),
            'grupousuario': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.GrupoUsuario']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'membro': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cadastro.Membro']"}),
            'publico': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'cadastro.lista': {
            'Meta': {'object_name': 'Lista'},
            'analytics': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nome': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'seo': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "u'A'", 'max_length': '1'}),
            'validade': ('django.db.models.fields.DateField', [], {})
        },
        'cadastro.listacadastro': {
            'Meta': {'ordering': "('lista', 'pessoa__nome')", 'object_name': 'ListaCadastro'},
            'dtinclusao': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lista': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cadastro.Lista']"}),
            'pessoa': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cadastro.Pessoa']"})
        },
        'cadastro.membro': {
            'Meta': {'ordering': "['nome']", 'object_name': 'Membro', '_ormbases': ['cadastro.Pessoa']},
            'aprovador': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'membro_aprovador'", 'null': 'True', 'to': "orm['auth.User']"}),
            'assinado': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'atividade_profissional': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'contrib_prox_pgto': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'contrib_tipo': ('django.db.models.fields.CharField', [], {'default': "'N'", 'max_length': '1'}),
            'contrib_valor': ('utils.fields.BRDecimalField', [], {'default': '0', 'max_digits': '7', 'decimal_places': '2'}),
            'cpf': ('django.db.models.fields.CharField', [], {'max_length': '14', 'null': 'True', 'blank': 'True'}),
            'dt_prefiliacao': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'dtnascimento': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'endereco': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'endereco_cep': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True', 'blank': 'True'}),
            'endereco_complemento': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'endereco_num': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'estadocivil': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'facebook_access_token': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'facebook_id': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'filiacao_partidaria': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'filiado': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'fundador': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'municipio_eleitoral': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'municipio_naturalidade': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'nome_da_mae': ('django.db.models.fields.CharField', [], {'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'pessoa_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cadastro.Pessoa']", 'unique': 'True', 'primary_key': 'True'}),
            'rg': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'secao_eleitoral': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'titulo_eleitoral': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'twitter_id': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'twitter_oauth_token': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'twitter_oauth_token_secret': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'uf_eleitoral': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['municipios.UF']", 'null': 'True', 'blank': 'True'}),
            'uf_naturalidade': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'uf_naturalidade'", 'null': 'True', 'to': "orm['municipios.UF']"}),
            'usuario': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'membro'", 'null': 'True', 'to': "orm['auth.User']"}),
            'zona_eleitoral': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'})
        },
        'cadastro.pessoa': {
            'Meta': {'ordering': "['nome']", 'object_name': 'Pessoa'},
            'apelido': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'celular': ('django.db.models.fields.CharField', [], {'max_length': '14', 'null': 'True', 'blank': 'True'}),
            'dtcadastro': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'municipio': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'nome': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'residencial': ('django.db.models.fields.CharField', [], {'max_length': '14', 'null': 'True', 'blank': 'True'}),
            'sexo': ('django.db.models.fields.CharField', [], {'default': "'O'", 'max_length': '1'}),
            'status_email': ('django.db.models.fields.CharField', [], {'default': "'N'", 'max_length': '1'}),
            'uf': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['municipios.UF']"})
        },
        'cms.article': {
            'Meta': {'ordering': "['-created_at']", 'object_name': 'Article'},
            'allow_comments': ('django.db.models.fields.CharField', [], {'default': "'N'", 'max_length': '1'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'content': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'conversions': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'created_at': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now'}),
            'header': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'keywords': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'sections': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['cms.Section']", 'null': 'True', 'through': "orm['cms.SectionItem']", 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '250', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'updated_at': ('django.db.models.fields.DateField', [], {'auto_now': 'True', 'blank': 'True'}),
            'views': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'cms.section': {
            'Meta': {'ordering': "['order', 'title']", 'object_name': 'Section'},
            'articles': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['cms.Article']", 'null': 'True', 'through': "orm['cms.SectionItem']", 'blank': 'True'}),
            'conversions': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'header': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keywords': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '250', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'views': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'cms.sectionitem': {
            'Meta': {'ordering': "['order']", 'object_name': 'SectionItem'},
            'article': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Article']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'db_index': 'True'}),
            'section': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Section']"})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'forum.grupo': {
            'Meta': {'object_name': 'Grupo'},
            'descricao': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nome': ('django.db.models.fields.CharField', [], {'max_length': '60'})
        },
        'forum.grupousuario': {
            'Meta': {'unique_together': "(('grupo', 'usuario'),)", 'object_name': 'GrupoUsuario'},
            'grupo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Grupo']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'usuario': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'municipios.uf': {
            'Meta': {'ordering': "(u'nome',)", 'object_name': 'UF'},
            'id_ibge': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'nome': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'regiao': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'uf': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        }
    }

    complete_apps = ['cadastro']