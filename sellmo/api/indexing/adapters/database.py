# Copyright (c) 2014, Adaptiv Design
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


import logging
from collections import OrderedDict

from django.apps import apps
from django.db import models
from django.db.models import Q
from django.db import transaction
from django.db import DEFAULT_DB_ALIAS, connections
from django.core.management import call_command
from django.utils import six

from sellmo.api import indexing


logger = logging.getLogger('sellmo')


class DatabaseIndexAdapter(indexing.IndexAdapter):
    
    # Shared among adapters
    _models = {}
    
    INDEX_TO_DB_FIELDS = {
        indexing.BooleanField: lambda field: (models.BooleanField, [], {}),
        indexing.CharField: lambda field: (models.CharField, [], {
            'max_length': field.max_length
        }),
        indexing.FloatField: lambda field: (models.FloatField, [], {}),
        indexing.IntegerField: lambda field: (models.IntegerField, [], {}),
        indexing.DecimalField: lambda field: (models.DecimalField, [], {
            # Introspection can't always resolve max_digits and decimal_places
            # (sqllite for instance)
            'max_digits': field.max_digits if field.max_digits is not None else 10,
            'decimal_places': field.decimal_places if field.decimal_places is not None else 5,
        }),
        indexing.ModelField: lambda field: (models.ForeignKey, [field.model], {})
    }
    
    DB_TO_INDEX_FIELDS = {
        'BooleanField': lambda field_params: (indexing.BooleanField, [], {}),
        'CharField': lambda field_params: (indexing.CharField, [], {
            'max_length': field_params['max_length']
        }),
        'FloatField': lambda field_params: (indexing.FloatField, [], {}),
        'IntegerField': lambda field_params: (indexing.IntegerField, [], {}),
        'DecimalField': lambda field_params: (indexing.DecimalField, [], {
            'max_digits': field_params['max_digits'],
            'decimal_places': field_params['decimal_places']
        }),
        'ForeignKey': lambda field_params: (indexing.ModelField, [field_params['model']], {}),
    }
    
    def supports_runtime_build(self):
        return False
        
    def db_field_for_index_field(self, index_field):
        if type(index_field) in self.INDEX_TO_DB_FIELDS:
            field_cls, args, kwargs = self.INDEX_TO_DB_FIELDS[index_field.__class__](index_field)
            return field_cls(*args, **dict({
                'blank': not index_field.required,
                'null': True
            }, **kwargs))
        raise TypeError(index_field)
        
    def index_field_for_db_field(self, field_type, field_params):
        if field_type in self.DB_TO_INDEX_FIELDS:
            field_cls, args, kwargs = self.DB_TO_INDEX_FIELDS[field_type](field_params)
            return field_cls(*args, **dict({
                'required': None
            }, **kwargs))
        raise TypeError(field_type)
        
    def index_model_factory(self, index, building=False):
        if index.name not in self._models:
            class Meta:
                app_label = index.model._meta.app_label
                db_table = self.get_index_db_table(index)
            attrs = {
                'Meta': Meta,
                '__module__': index.__module__
            }
            
            for field_name, index_field in six.iteritems(index.fields if building else index.introspected_fields):
                db_field = self.db_field_for_index_field(index_field)
                if db_field:
                    attrs[field_name] = db_field
    
            model = type('%sIndex' % index.name, (models.Model,), attrs)
            self._models[index.name] = model
        return self._models[index.name]    
    
    def get_index_db_table(self, index):
        info = (index.model._meta.app_label, index.name)
        return "%s_%s_index" % info
        
    def get_db_connection(self):
        return connections[DEFAULT_DB_ALIAS]
        
    def get_db_models(self):
        db_models = {}
        for model in apps.get_models():
            db_models[model._meta.db_table] = model
        return db_models
        
    def introspect_index(self, index):
        
        connection = self.get_db_connection()
        db_table = self.get_index_db_table(index)
        db_models = self.get_db_models()
        
        exists = False
        
        # Map models to db_name
        fields = {}
        with connection.cursor() as cursor:
            
            try:
                relations = connection.introspection.get_relations(cursor, db_table)
            except NotImplementedError:
                raise Exception("")
            try:
                indexes = connection.introspection.get_indexes(cursor, db_table)
            except NotImplementedError:
                raise Exception("")
            try:
                constraints = connection.introspection.get_constraints(cursor, db_table)
            except NotImplementedError:
                raise Exception("")
            
            for i, row in enumerate(connection.introspection.get_table_description(cursor, db_table)):
                
                # We got a result, index exists
                exists = True
                
                column_name = row[0]
                
                # Ignore fixed fields
                if column_name in ['id', 'document_id']:
                    continue
                
                field_type = None
                field_params = OrderedDict()
                
                if i in relations:
                    field_type = 'ForeignKey'
                    model = db_models.get(relations[i][1], None)
                    if not model:
                        raise Exception("")
                    if not column_name.endswith('_id'):
                        raise Exception("")
                    column_name = column_name[:-3]
                    field_params['model'] = model
                else:
                    try:
                        field_type = connection.introspection.get_field_type(row[1], row)
                    except KeyError:
                        raise Exception("")
                    
                    # This is a hook for data_types_reverse to return a tuple of
                    # (field_type, field_params_dict).
                    if type(field_type) is tuple:
                        field_type, new_params = field_type
                        field_params.update(new_params)
                    
                    # Add max_length for all CharFields.
                    if field_type == 'CharField' and row[3]:
                        field_params['max_length'] = int(row[3])
                    
                    if field_type == 'DecimalField':
                        if row[4] is None or row[5] is None:
                            field_params['max_digits'] = row[4] if row[4] is not None else None
                            field_params['decimal_places'] = row[5] if row[5] is not None else None
                        else:
                            field_params['max_digits'] = row[4]
                            field_params['decimal_places'] = row[5]
                    
                field_params['null'] = row[6]
                            
                index_field = self.index_field_for_db_field(field_type, field_params)
                if index_field:
                    fields[column_name] = index_field
        
        if exists:
            return fields
        return False
        
    def initialize_index(self, index):
        model = self.index_model_factory(index)
        
        # Document field combined with all varieties field
        # are unique, we can use them to query existing records
        # WE EXPLICITLY DO NOT use this in our Model's Meta
        # as we don't want to enforce any db's constraints and
        # thus keep our table usage flexible.
        unique_together = { 
            field_name: field 
            for field_name, field in six.iteritems(index.fields)
            if field_name == 'document' or field.varieties
        }
        
        # Find unused fields in our table.
        unused_fields = {
            field_name: field
            for field_name, field in six.iteritems(index.introspected_fields)
            if field_name not in index.fields
        }
        
        index._unique_together = unique_together
        index._unused_fields = unused_fields
        

    def build_index(self, index):
        model = self.index_model_factory(index, building=True)
        call_command('makemigrations', index.model._meta.app_label)
        call_command('migrate', index.model._meta.app_label)
        
    def rebuild_index(self, index, added_fields, deleted_fields, changed_fields):
        self.build_index(index)

    def update_index(self, index, documents):
        model = self.index_model_factory(index)
        with transaction.atomic():
            
            # We won't allow records who utilize unused fields
            # Delete them so are always getting unique query results.
            if index._unused_fields:
                q = Q()
                for field_name in six.iterkeys(index._unused_fields):
                    q |= Q(**{'%s__isnull' % field_name: False})
                invalid = model.objects.filter(q, document__in=documents)
                invalid.delete()
                
            # We also won't allow records who have haven't all 
            # _unique_together fields populated. Clean them up.
            q = Q()
            for field_name in six.iterkeys(index._unique_together):
                q |= Q(**{'%s__isnull' % field_name: True})
            stale = model.objects.filter(q, document__in=documents)
            stale.delete()
            
            for document in documents:
                records = index.build_records(document)
                for record in records:
                    model.objects.update_or_create(**dict(defaults=record, **{
                        field_name: record[field_name]
                        for field_name in six.iterkeys(index._unique_together)
                    }))   

    def clear_index(self, index, documents):
        """
        Clears the index for each document from the given iterable.
        """
        raise NotImplementedError()

    def search_index(self, index, query):
        """
        Searches the index
        """
        raise NotImplementedError()