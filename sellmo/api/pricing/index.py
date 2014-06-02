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


import re
import inspect

from sellmo import modules

from django.db import models
from django.db.models.query import QuerySet
from django.db.models import Q
from django.utils import six


__all__ = [
    'PriceIndex',
    'PrefetchedPriceIndex',
]


camelize = re.compile(r'(?!^)_([a-zA-Z])')


def _make_indexable(queryset, indexes, through):
    if isinstance(queryset, IndexedQuerySet):
        raise Exception("This is already an indexed queryset")
    # Decide correct mro
    if issubclass(queryset.__class__, QuerySet):
        # We got a subclass of QuerySet
        # Subclass -> IndexedQuerySet -> QuerySet
        bases = (queryset.__class__, IndexedQuerySet)
    else:
        # We got a QuerySet
        bases = (IndexedQuerySet,)

    # Construct new QuerySet class and clone to this class
    indexed = queryset._clone(klass=type('IndexedQuerySet', bases, {}))
    indexed._indexes = indexes._clone()
    indexed._through = through
    indexed.index = PrefetchedPriceIndex(through)
    return indexed


def _get_query_ordering(query):
    if query.extra_order_by:
        return list(query.extra_order_by)
    elif query.order_by:
        return list(query.order_by)
    elif query.default_ordering and query.get_meta().ordering:
        return list(query.get_meta().ordering)
    return []


class IndexedQuerySet(QuerySet):

    _is_sliced = False
    _indexes = None
    _through = None

    def __get_ordering__(self):
        # indexes order precedes our order
        for order in _get_query_ordering(self._indexes.query):
            yield order
        
        for order in _get_query_ordering(self.query):
            desc = False
            if order.startswith('-'):
                order = order[1:]
                desc = True
            if desc:
                yield '-{0}__{1}'.format(self._through, order)
            else:
                yield '{0}__{1}'.format(self._through, order)
            
    def __get_select_related__(self):
        yield self._through
        if isinstance(self.query.select_related, bool):
            if self.query.select_related:
                pass
        else:
            for field, _ in self.query.select_related.iteritems():
                yield '{0}__{1}'.format(self._through, field)
    
    def __getitem__(self, k):
        clone = self._clone()
        clone._indexes = clone._query_indexes()[k]
        clone._is_sliced = True
        if isinstance(k, slice):
            return list(clone)
        
        clone._indexes = [clone._indexes]
        return list(clone)[0]
    
    def _query_indexes(self):
        if self._is_sliced:
            return self._indexes
         
        # At this point we will filter our indexes query against ourselves.   
        # This won't cause any recursion since Django generates a nested
        # query. No actual iteration on this query will occur.
        qargs = {
            '{0}__in'.format(self._through): self
        }
        return self._indexes.filter(**qargs).select_related(
                            *self.__get_select_related__()) \
                            .order_by(*self.__get_ordering__())
    
    def indexes(self, func):
        if self._is_sliced:
            raise Exception("Cannot alter indexes queryset")
        clone = self._clone()
        clone._indexes = func(clone._indexes)
        return clone
    
    def join(self):
        for obj in self._query_indexes():
            self.index.index(getattr(obj, self._through).pk, obj)
            yield getattr(obj, self._through), obj
    
    def iterator(self):
        out = []
        for a, b in self.join():
            yield a
    
    def count(self):
        return self._query_indexes().count()
        
    def _clone(self, *args, **kwargs):
        clone = super(IndexedQuerySet, self)._clone(*args, **kwargs)
        clone._indexes = self._indexes._clone()
        clone._through = self._through
        clone._is_sliced = self._is_sliced
        
        # We explicitely do not clone the index, it can safely be shared
        # accross querysets
        clone.index = self.index
        
        return clone
        

class PrefetchedPriceIndex(object):

    def __init__(self, through):
        self.through = through
        self.indexes = {}

    def lookup(self, **kwargs):
        if self.through not in kwargs:
            raise Exception("through '{0}' not given.".format(self.through))
        return self.indexes[kwargs[self.through].pk].price

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
            unique_together = tuple(value['field_name']
                                    for value in self.kwargs.values())

        name = '{0}Index'.format(camelize.sub(
            lambda m: m.group(1).upper(), self.identifier.title()))
        attr_dict = {
            'Meta': Meta,
            '__module__': modules.pricing.PriceIndexBase.__module__
        }

        for key, value in self.kwargs.iteritems():
            field = value.get('field', None)
            if field:
                field_name = value.get('field_name')
                attr_dict[field_name] = field

        model = type(name, (modules.pricing.PriceIndexBase,), attr_dict)
        model = modules.pricing.make_stampable(
            model=model,
            properties=['price']
        )

        # Now finalize
        class Meta(model.Meta):
            pass

        attr_dict = {
            'Meta': Meta,
            '__module__': model.__module__
        }

        model = type(name, (model,), attr_dict)
        self._model = model

    def _get_query(self, through=None, nullable=False, **kwargs):
        fargs, complete = self._get_field_args(through=through, **kwargs)
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

    def _get_field_args(self, through=None, **kwargs):
        fargs = {}
        complete = True
        for key, value in self.kwargs.iteritems():
            if key == through:
                continue
            field_name = value['field_name']
            transform = value['transform']
            if key in kwargs and kwargs[key] is not None:
                fargs[field_name] = kwargs[
                    key] if not transform else transform(kwargs[key])
            elif value['required']:
                complete = False
            else:
                fargs[field_name] = None
        return fargs, complete

    def add_kwarg(self, name, field=None, field_name=None, required=True, 
                  transform=None, default=None, model=None):
        if name in ('through', 'nullable'):
            raise Exception(
                "Resereved kwarg name '{0}"
                .format(name))
        if name in self.kwargs:
            raise Exception(
                "Index '{0}' already has a kwarg '{1}'"
                .format(self, name))
        if not field_name:
            field_name = name
        if self._model is not None:
            raise Exception(
                "Index '{0}' is already build."
                .format(self))
        if not required and field.null is False:
            raise Exception(
                "Index '{0}' field '{1}' must be nullable."
                .format(self, field_name))

        self.kwargs[name] = {
            'field_name': field_name,
            'required': required,
            'field': field,
            'transform': transform,
            'default': default,
            'model': model,
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

    def query(self, queryset, through, **kwargs):
        q, complete = self._get_query(through=through, **kwargs)
        if complete:
            queryset = _make_indexable(
                queryset, self.model.objects.filter(q), through)
        return queryset
        
    def make_indexable(self, queryset, through):
        return _make_indexable(queryset, self.model.objects.all(), through)

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
                raise ValueError(
                    "Index '{0}' update kwarg '{1}' "
                    "is not valid."
                    .format(self, key))
            if not isinstance(value, (list, tuple, QuerySet)):
                raise TypeError(
                    "Index '{0}' update kwarg '{1}' "
                    "must be a list or QuerySet."
                    .format(self, key))
            if self.kwargs[key].get('model', None) is not None:
                model = self.kwargs[key]['model']
                if isinstance(value, QuerySet) and not value.model is model:
                    raise ValueError(
                        "Index '{0}' update kwarg '{1}' "
                        "is not a valid QuerySet."
                        .format(self, key))
                elif not isinstance(value, QuerySet):
                    # Yes this is safe
                    kwargs[key] = model.objects.filter(
                        pk__in=[el.pk for el in value])

        # Now update with provided kwargs
        modules.pricing.update_index(
            index=self.identifier, invalidations=invalidations, **kwargs)

    @property
    def model(self):
        return self._model

    def __repr__(self):
        return self.identifier
