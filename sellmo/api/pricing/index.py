# Copyright (c) 2012, Adaptiv Design
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
#    * Neither the name of the <ORGANIZATION> nor the names of its contributors may
# be used to endorse or promote products derived from this software without specific
# prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import re
import inspect

#

from sellmo import modules

#

from django.db import models
from django.db.models.query import QuerySet
from django.db.models import Q
from django.utils import six

#

__all__ = [
    'PriceIndex',
    'PrefetchedPriceIndex',
]

#

camelize = re.compile(r'(?!^)_([a-zA-Z])')

#

class IndexedQuerySet(QuerySet):

    _order_indexes_by = []
    _is_indexed = True
    _is_sliced = False

    def _get_order(self):
        ordering = []
        if self.query.extra_order_by:
            ordering = list(self.query.extra_order_by) 
        elif self.query.order_by:
            ordering = list(self.query.order_by)
        elif self.query.default_ordering and self.query.get_meta().ordering:
            ordering = list(self.query.get_meta().ordering)

        for order in self._order_indexes_by:
            yield order

        for order in ordering:
            desc = False
            if order.startswith('-'):
                order = order[1:]
                desc = True
            if desc:
                yield '-{0}__{1}'.format(self._relation, order)
            else:
                yield '{0}__{1}'.format(self._relation, order)

    def __getitem__(self, k):
        clone = self._clone()
        clone._indexes = clone._get_indexed()[k]
        clone._is_sliced = True
        return list(clone)

    def _get_indexed(self):
        if self._is_sliced:
            return self._indexes
        qargs = {
            '{0}__in'.format(self._relation) : self
        }
        return self._indexes.filter(**qargs).select_related(self._relation).order_by(*self._get_order())

    def iterator(self):
        out = []
        for obj in self._get_indexed():
            related = getattr(obj, self._relation)
            out.append(related)
            self.index.index(related.pk, obj)
        return out

    def count(self):
        return self._get_indexed().count()

    def order_indexes_by(self, *field_names):
        clone = self._clone()
        clone._order_indexes_by = list(field_names)
        return clone

    def _clone(self, *args, **kwargs):
        clone = super(IndexedQuerySet, self)._clone(*args, **kwargs)
        clone._indexes = self._indexes._clone()
        clone._relation = self._relation
        clone._order_indexes_by = self._order_indexes_by
        clone._is_sliced = self._is_sliced
        # We explicitely do not clone the index, it can safely be shared accross querysets
        clone.index = self.index
        return clone

def make_indexed(queryset, indexes, relation):
    # Decide correct mro
    if issubclass(queryset.__class__, QuerySet):
        # We got a Subclass of QuerySet
        # Subclass -> IndexedQuerySet -> QuerySet
        bases = (queryset.__class__, IndexedQuerySet)
    else:
        # We got a QuerySet
        bases = (IndexedQuerySet,)

    # Construct new QuerySet class and clone to this class
    indexed = queryset._clone(klass=type('IndexedQuerySet', bases, {}))
    indexed._indexes = indexes
    indexed._relation = relation
    indexed.index = PrefetchedPriceIndex(relation)
    return indexed

class PrefetchedPriceIndex(object):
    def __init__(self, relation):
        self.relation = relation
        self.indexes = {}

    def lookup(self, **kwargs):
        if self.relation not in kwargs:
            raise Exception("Relation '{0}' not given.".format(self.relation))
        return self.indexes[kwargs[self.relation].pk].price

    def index(self, pk, index):
        self.indexes[pk] = index

class PriceIndex(object):
    def __init__(self, identifier):
        self.identifier = identifier
        self.kwargs = {}
        self._model = None

    def _build(self):
        class Meta(modules.pricing.PriceIndexBase.Meta):
            abstract = True
            unique_together = tuple(value['field_name'] for value in self.kwargs.values())

        name = '{0}Index'.format(camelize.sub(lambda m: m.group(1).upper(), self.identifier.title()))
        attr_dict = {
            'Meta' : Meta,
            '__module__': modules.pricing.PriceIndexBase.__module__
        }

        for key, value in self.kwargs.iteritems():
            field = value.get('field', None)
            if field:
                field_name = value.get('field_name')
                attr_dict[field_name] = field

        model = type(name, (modules.pricing.PriceIndexBase,), attr_dict)
        model = modules.pricing.make_stampable(
            model = model,
            properties = ['price']
        )

        # Now finalize
        class Meta(model.Meta):
            pass

        attr_dict = {
            'Meta' : Meta,
            '__module__': model.__module__
        }

        model = type(name, (model,), attr_dict)
        self._model = model

    def _get_query(self, relation=None, nullable=False, **kwargs):
        fargs, complete = self._get_field_args(relation=relation, **kwargs)
        orm_lookup = {}
        for key, value in fargs.iteritems():
            if value is None:
                if nullable:
                    continue
                key = '{0}__isnull'.format(key)
                value = True
            if isinstance(value, (tuple, list, QuerySet)):
                key = '{0}__in'.format(key)
            orm_lookup[key] = value
        return Q(**orm_lookup), complete

    def _get_field_args(self, relation=None, **kwargs):
        fargs = {}
        complete = True
        for key, value in self.kwargs.iteritems():
            if key == relation:
                continue
            field_name = value['field_name']
            transform = value['transform']
            if key in kwargs and kwargs[key] is not None:
                fargs[field_name] = kwargs[key] if not transform else transform(kwargs[key])
            elif value['required']:
                complete = False
            else:
                fargs[field_name] = None
        return fargs, complete

    def add_kwarg(self, name, field=None, field_name=None, required=True, transform=None, default=None):
        if name in ('relation', 'nullable'):
            raise Exception("Resereved kwarg name '{0}".format(name))
        if name in self.kwargs:
            raise Exception("Index '{0}' already has a kwarg '{1}'".format(self, name))
        if not field_name:
            field_name = name
        if self._model is not None:
            raise Exception("Index '{0}' is already build.".format(self))
        if not required and field.null is False:
            raise Exception("Index '{0}' field '{1}' must be nullable.".format(self, field_name))
    
        self.kwargs[name] = {
            'field_name' : field_name,
            'required' : required,
            'field' : field,
            'transform' : transform,
            'default' : default
        }
    
    def is_kwarg(self, name):
        return name in self.kwargs

    def index(self, price, **kwargs):
        q, complete = self._get_query(**kwargs)
        if complete:
            try:
                return self.model.objects.get(q).delete()
            except self.model.DoesNotExist:
                pass
        fargs, complete = self._get_field_args(**kwargs)
        if complete:
            obj = self.model(**fargs)
            obj.price = price
            obj.save()
            return True
        return False

    def lookup(self, **kwargs):
        q, complete = self._get_query(**kwargs)
        if complete:
            try:
                return self.model.objects.get(q).price
            except self.model.DoesNotExist:
                pass
        return None

    def query(self, queryset, relation, **kwargs):
        q, complete = self._get_query(relation=relation, **kwargs)
        if complete:
            queryset = make_indexed(queryset, self.model.objects.filter(q), relation)
        return queryset
        
    def update(self, **kwargs):
        # First query invalidations
        q, complete = self._get_query(nullable=True, **kwargs)
        invalidations = self.model.objects.filter(q)
        
        # Fill defaults
        for key, value in self.kwargs.iteritems():
            if key not in kwargs and value['default']:
                default = value['default']
                if callable(default):
                    kwargs[key] = default()
                else:
                    kwargs[key] = default
        
        # Make sure kwargs is either a QuerySet, or a list
        for key, value in kwargs.iteritems():
            if not self.is_kwarg(key):
                raise ValueError("Index '{0}' update kwarg '{1}' is not valid.".format(self, key))
            if not isinstance(value, (list, tuple, QuerySet)):
                raise TypeError("Index '{0}' update kwarg '{1}' must be a list or QuerySet.".format(self, key))
        
        # Now update with provided kwargs
        modules.pricing.update_index(index=self.identifier, invalidations=invalidations, **kwargs)

    @property
    def model(self):
        return self._model

    def __repr__(self):
        return self.identifier