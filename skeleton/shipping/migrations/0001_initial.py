# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'BasicMethod'
        db.create_table('shipping_basicmethod', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('carrier', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('shipping', ['BasicMethod'])

        # Adding model 'TieredMethod'
        db.create_table('shipping_tieredmethod', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('carrier', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('shipping', ['TieredMethod'])

        # Adding model 'TieredMethodTier'
        db.create_table('shipping_tieredmethodtier', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('method', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shipping.TieredMethod'])),
            ('amount', self.gf('django.db.models.fields.DecimalField')(max_digits=9, decimal_places=2)),
            ('tier', self.gf('django.db.models.fields.DecimalField')(max_digits=9, decimal_places=2)),
        ))
        db.send_create_signal('shipping', ['TieredMethodTier'])


    def backwards(self, orm):
        # Deleting model 'BasicMethod'
        db.delete_table('shipping_basicmethod')

        # Deleting model 'TieredMethod'
        db.delete_table('shipping_tieredmethod')

        # Deleting model 'TieredMethodTier'
        db.delete_table('shipping_tieredmethodtier')


    models = {
        'shipping.basicmethod': {
            'Meta': {'object_name': 'BasicMethod'},
            'carrier': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'shipping.tieredmethod': {
            'Meta': {'object_name': 'TieredMethod'},
            'carrier': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'shipping.tieredmethodtier': {
            'Meta': {'object_name': 'TieredMethodTier'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shipping.TieredMethod']"}),
            'tier': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '2'})
        }
    }

    complete_modules = ['shipping']