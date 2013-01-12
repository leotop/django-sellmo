# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ColorAttribute'
        db.create_table('product_colorattribute', (
            ('attribute_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['product.Attribute'], unique=True, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=60)),
            ('color_code', self.gf('django.db.models.fields.CharField')(max_length=6)),
        ))
        db.send_create_signal('product', ['ColorAttribute'])

        # Adding model 'SimpleAttribute'
        db.create_table('product_simpleattribute', (
            ('attribute_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['product.Attribute'], unique=True, primary_key=True)),
            ('display', self.gf('django.db.models.fields.CharField')(max_length=120)),
        ))
        db.send_create_signal('product', ['SimpleAttribute'])


    def backwards(self, orm):
        # Deleting model 'ColorAttribute'
        db.delete_table('product_colorattribute')

        # Deleting model 'SimpleAttribute'
        db.delete_table('product_simpleattribute')


    models = {
        'category.category': {
            'Meta': {'ordering': "['order']", 'object_name': 'Category'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['category.Category']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '80'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'product.attribute': {
            'Meta': {'ordering': "['content_type', 'value']", 'object_name': 'Attribute'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '80'})
        },
        'product.colorattribute': {
            'Meta': {'ordering': "['content_type', 'value']", 'object_name': 'ColorAttribute', '_ormbases': ['product.Attribute']},
            'attribute_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['product.Attribute']", 'unique': 'True', 'primary_key': 'True'}),
            'color_code': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'})
        },
        'product.option': {
            'Meta': {'ordering': "['variable', 'sort_order']", 'unique_together': "(('variable', 'attribute'),)", 'object_name': 'Option'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['product.Attribute']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sort_order': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'variable': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['product.Variable']"})
        },
        'product.product': {
            'Meta': {'ordering': "['slug']", 'object_name': 'Product'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'category': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'products'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['category.Category']"}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True'}),
            'featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True'}),
            'sku': ('django.db.models.fields.CharField', [], {'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '80'}),
            'tax': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tax.Tax']", 'null': 'True', 'blank': 'True'})
        },
        'product.simpleattribute': {
            'Meta': {'ordering': "['content_type', 'value']", 'object_name': 'SimpleAttribute', '_ormbases': ['product.Attribute']},
            'attribute_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['product.Attribute']", 'unique': 'True', 'primary_key': 'True'}),
            'display': ('django.db.models.fields.CharField', [], {'max_length': '120'})
        },
        'product.simpleproduct': {
            'Meta': {'ordering': "['slug']", 'object_name': 'SimpleProduct', '_ormbases': ['product.Product']},
            'custom_options': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['product.Option']", 'symmetrical': 'False', 'blank': 'True'}),
            'product_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['product.Product']", 'unique': 'True', 'primary_key': 'True'})
        },
        'product.simpleproductvariant': {
            'Meta': {'ordering': "['slug']", 'object_name': 'SimpleProductVariant', '_ormbases': ['product.SimpleProduct']},
            'options': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['product.Option']", 'symmetrical': 'False'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'variants'", 'to': "orm['product.SimpleProduct']"}),
            'simpleproduct_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['product.SimpleProduct']", 'unique': 'True', 'primary_key': 'True'})
        },
        'product.variable': {
            'Meta': {'ordering': "['name']", 'object_name': 'Variable'},
            'attributes': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['product.Attribute']", 'through': "orm['product.Option']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'})
        },
        'tax.tax': {
            'Meta': {'object_name': 'Tax'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'rate': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '2'})
        }
    }

    complete_modules = ['product']