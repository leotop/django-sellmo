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


from django.db import models
from django.db import DEFAULT_DB_ALIAS, connections
from django.core.management import call_command
from django.utils import six

from sellmo.api.indexing.adapters import IndexAdapter
from sellmo.api.indexing.fields import (BooleanField, CharField,
                                        IntegerField, ModelField)


_models = {}


INDEX_TO_DB_FIELDS = {
    BooleanField: lambda field: (models.BooleanField, [], {}),
    CharField: lambda field: (models.CharField, [], {'max_length': 255}),
    IntegerField: lambda field: (models.IntegerField, [], {}),
    ModelField: lambda field: (models.ForeignKey, [field.model], {})
}


def get_index_db_table(index):
    info = (index.model._meta.app_label, index.name)
    return "%s_%s_index" % info
    
    
def db_field_for_index_field(index_field):
    if index_field.__class__ in INDEX_TO_DB_FIELDS:
        field_cls, args, kwargs = INDEX_TO_DB_FIELDS[index_field.__class__](index_field)
        return field_cls(*args, **dict({
            'null': not index_field.required
        }, **kwargs))
    return None


def index_model_factory(index):
    if index.name not in _models:
        class Meta:
            app_label = index.model._meta.app_label
            db_table = get_index_db_table(index)
        attrs = {
            'Meta': Meta,
            '__module__': index.__module__
        }
        
        for field_name, index_field in six.iteritems(index.fields):
            db_field = db_field_for_index_field(index_field)
            if db_field:
                attrs[field_name] = db_field
        
        model = type('%sIndex' % index.name, (models.Model,), attrs)
        _models[index.name] = model
    return _models[index.name]


class DatabaseIndexAdapter(IndexAdapter):
    
    def supports_runtime_build(self):
        return False
        
    def introspect_index(self, index):
        connection = connections[DEFAULT_DB_ALIAS]
        db_table = get_index_db_table(index)
        exists = False
        
        fields = []
        with connection.cursor() as cursor:
            for row in connection.introspection.get_table_description(cursor, db_table):
                exists = True
                column_name = row[0]
                if column_name not in ['id', 'document_id']:
                    print row
        if exists:
            return fields
        return False
        
    def initialize_index(self, index):
        model = index_model_factory(index)

    def build_index(self, index):
        model = index_model_factory(index)
        call_command('makemigrations', index.model._meta.app_label)
        call_command('migrate', index.model._meta.app_label)
        
    def rebuild_index(self, index, added_fields=None, deleted_fields=None):
        self.build_index(index)

    def update_index(self, index, documents):
        """
        (Re)indexes each document from the given iterable.
        """
        raise NotImplementedError()

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