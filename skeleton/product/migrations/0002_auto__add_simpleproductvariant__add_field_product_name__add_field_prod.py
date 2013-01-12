# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'SimpleProductVariant'
        db.create_table('product_simpleproductvariant', (
            ('simpleproduct_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['product.SimpleProduct'], unique=True, primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(related_name='variants', to=orm['product.SimpleProduct'])),
        ))
        db.send_create_signal('product', ['SimpleProductVariant'])

        # Adding M2M table for field options on 'SimpleProductVariant'
        db.create_table('product_simpleproductvariant_options', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('simpleproductvariant', models.ForeignKey(orm['product.simpleproductvariant'], null=False)),
            ('option', models.ForeignKey(orm['product.option'], null=False))
        ))
        db.create_unique('product_simpleproductvariant_options', ['simpleproductvariant_id', 'option_id'])

        # Adding field 'Product.name'
        db.add_column('product_product', 'name',
                      self.gf('django.db.models.fields.CharField')(max_length=120, null=True),
                      keep_default=False)

        # Adding field 'Product.sku'
        db.add_column('product_product', 'sku',
                      self.gf('django.db.models.fields.CharField')(max_length=60, null=True, blank=True),
                      keep_default=False)

        # Adding M2M table for field custom_options on 'SimpleProduct'
        db.create_table('product_simpleproduct_custom_options', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('simpleproduct', models.ForeignKey(orm['product.simpleproduct'], null=False)),
            ('option', models.ForeignKey(orm['product.option'], null=False))
        ))
        db.create_unique('product_simpleproduct_custom_options', ['simpleproduct_id', 'option_id'])


    def backwards(self, orm):
        # Deleting model 'SimpleProductVariant'
        db.delete_table('product_simpleproductvariant')

        # Removing M2M table for field options on 'SimpleProductVariant'
        db.delete_table('product_simpleproductvariant_options')

        # Deleting field 'Product.name'
        db.delete_column('product_product', 'name')

        # Deleting field 'Product.sku'
        db.delete_column('product_product', 'sku')

        # Removing M2M table for field custom_options on 'SimpleProduct'
        db.delete_table('product_simpleproduct_custom_options')


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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True'}),
            'sku': ('django.db.models.fields.CharField', [], {'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '80'}),
            'tax': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tax.Tax']", 'null': 'True', 'blank': 'True'})
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