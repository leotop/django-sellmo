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

#

__all__ = [
	'PriceIndex',
]

#

camelize = re.compile(r'(?!^)_([a-zA-Z])')

#

class IndexedQuerySet(QuerySet):
	
	_order_indexes_by = []
	_is_indexed = True
	index = {}
	
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
		return list(self)[k]
	
	def _get_indexed(self):
		qargs = {
			'{0}__in'.format(self._relation) : self
		}
		return self._indexes.select_related(self._relation).order_by(*self._get_order())
	
	def iterator(self):
		self.index = PopulatedPriceIndex()
		out = []
		for obj in self._get_indexed():
			related = getattr(obj, self._relation)
			out.append(related)
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
	return indexed
	
class PopulatedPriceIndex(object):
	def __init__(self):
		pass

class PriceIndex(object):
	def __init__(self, identifier):
		self.identifier = identifier
		self.kwargs = {
			'currency' : {
				'field_name' : 'price_currency',
				'required' : True
			}
		}
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
		
	def _get_query(self, relation=None, **kwargs):
		fargs, complete = self._get_field_args(relation=relation, **kwargs)
		orm_lookup = {}
		for key, value in fargs.iteritems():
			if value is None:
				key = '{0}__isnull'.format(key)
				value = True
			orm_lookup[key] = value
		return Q(**orm_lookup), complete
		
	def _get_field_args(self, relation=None, **kwargs):
		fargs = {}
		complete = True
		for key, value in self.kwargs.iteritems():
			if key == relation:
				continue
			field_name = value['field_name']
			if key in kwargs and kwargs[key] is not None:
				fargs[field_name] = kwargs[key]
			elif value['required']:
				complete = False
			else:
				fargs[field_name] = None
		return fargs, complete
		
	def add_kwarg(self, name, field, field_name=None, required=True):
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
			'field' : field
		}
		
	def index(self, price, **kwargs):
		existing = self.lookup(**kwargs)
		if existing:
			existing.delete()
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
		
	def invalidate(self, **kwargs):
		q, complete = self._get_query(**kwargs)
		self.model.objects.filter(q).invalidate()
		
	def query(self, queryset, relation, **kwargs):
		q, complete = self._get_query(relation, **kwargs)
		if complete:
			queryset = make_indexed(queryset, self.model.objects.filter(q), relation)
		return queryset
		
	@property
	def model(self):
		return self._model
			
	def __repr__(self):
		return self.identifier