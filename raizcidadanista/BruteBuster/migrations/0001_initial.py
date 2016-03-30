# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'FailedAttempt'
        db.create_table('BruteBuster_failedattempt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('IP', self.gf('django.db.models.fields.IPAddressField')(max_length=15, null=True)),
            ('failures', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('BruteBuster', ['FailedAttempt'])

        # Adding unique constraint on 'FailedAttempt', fields ['username', 'IP']
        db.create_unique('BruteBuster_failedattempt', ['username', 'IP'])

        # Adding model 'FailedURLAttempt'
        db.create_table('BruteBuster_failedurlattempt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('IP', self.gf('django.db.models.fields.IPAddressField')(max_length=15, unique=True, null=True)),
            ('failures', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('BruteBuster', ['FailedURLAttempt'])


    def backwards(self, orm):
        # Removing unique constraint on 'FailedAttempt', fields ['username', 'IP']
        db.delete_unique('BruteBuster_failedattempt', ['username', 'IP'])

        # Deleting model 'FailedAttempt'
        db.delete_table('BruteBuster_failedattempt')

        # Deleting model 'FailedURLAttempt'
        db.delete_table('BruteBuster_failedurlattempt')


    models = {
        'BruteBuster.failedattempt': {
            'IP': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True'}),
            'Meta': {'ordering': "['-timestamp']", 'unique_together': "(('username', 'IP'),)", 'object_name': 'FailedAttempt'},
            'failures': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'BruteBuster.failedurlattempt': {
            'IP': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'unique': 'True', 'null': 'True'}),
            'Meta': {'ordering': "['-timestamp']", 'object_name': 'FailedURLAttempt'},
            'failures': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['BruteBuster']