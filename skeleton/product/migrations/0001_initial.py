# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Attribute'
        db.create_table('product_attribute', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True)),
            ('value', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=80)),
        ))
        db.send_create_signal('product', ['Attribute'])

        # Adding model 'Variable'
        db.create_table('product_variable', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=80)),
        ))
        db.send_create_signal('product', ['Variable'])

        # Adding model 'Option'
        db.create_table('product_option', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sort_order', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('variable', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['product.Variable'])),
            ('attribute', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['product.Attribute'])),
        ))
        db.send_create_signal('product', ['Option'])

        # Adding unique constraint on 'Option', fields ['variable', 'attribute']
        db.create_unique('product_option', ['variable_id', 'attribute_id'])

        # Adding model 'Product'
        db.create_table('product_product', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('featured', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=80)),
            ('tax', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tax.Tax'], null=True, blank=True)),
        ))
        db.send_create_signal('product', ['Product'])

        # Adding M2M table for field category on 'Product'
        db.create_table('product_product_category', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('product', models.ForeignKey(orm['product.product'], null=False)),
            ('category', models.ForeignKey(orm['category.category'], null=False))
        ))
        db.create_unique('product_product_category', ['product_id', 'category_id'])

        # Adding model 'SimpleProduct'
        db.create_table('product_simpleproduct', (
            ('product_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['product.Product'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('product', ['SimpleProduct'])


    def backwards(self, orm):
        # Removing unique constraint on 'Option', fields ['variable', 'attribute']
        db.delete_unique('product_option', ['variable_id', 'attribute_id'])

        # Deleting model 'Attribute'
        db.delete_table('product_attribute')

        # Deleting model 'Variable'
        db.delete_table('product_variable')

        # Deleting model 'Option'
        db.delete_table('product_option')

        # Deleting model 'Product'
        db.delete_table('product_product')

        # Removing M2M table for field category on 'Product'
        db.delete_table('product_product_category')

        # Deleting model 'SimpleProduct'
        db.delete_table('product_simpleproduct')


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
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '80'}),
            'tax': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tax.Tax']", 'null': 'True', 'blank': 'True'})
        },
        'product.simpleproduct': {
            'Meta': {'ordering': "['slug']", 'object_name': 'SimpleProduct', '_ormbases': ['product.Product']},
            'product_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['product.Product']", 'unique': 'True', 'primary_key': 'True'})
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