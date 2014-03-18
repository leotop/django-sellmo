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

import types
from threading import local
from collections import deque

#

from django.db import models
from django.db.models.query import QuerySet
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.util import quote
from django.utils.functional import allow_lazy

#

_local = local()

class PolymorphicOverride(object):
    
    def __init__(self, polymorphic=True):
        self._polymorphic = polymorphic
    
    def __enter__(self):
        if not hasattr(_local, 'overrides'):
            _local.overrides = deque()
        _local.overrides.append(self._polymorphic)
        
    def __exit__(self, exc_type, exc_value, traceback):
        _local.overrides.pop()
        if not _local.overrides:
            del _local.overrides

class PolymorphicQuerySet(QuerySet):

    _downcast = False

    def __init__(self, *args, **kwargs):
        if kwargs.has_key('downcast'):
            self._downcast = kwargs.pop('downcast')
        super(PolymorphicQuerySet, self).__init__(*args, **kwargs)

    def iterator(self):
        override = None
        if hasattr(_local, 'overrides'):
            override = _local.overrides[-1] # peek
        downcast = (
            self._downcast and override is not False
            or override is True
        )
        
        if not downcast:
            return super(PolymorphicQuerySet, self).iterator()
        else:
            content_types = {}
            content_types_elements = {}
            order = []
            downcasts = {}
            result = []

            for el in super(PolymorphicQuerySet, self).iterator():
                if not content_types.has_key(el.content_type_id):
                    content_types[el.content_type_id] = el.content_type
                    content_types_elements[el.content_type_id] = []
                content_types_elements[el.content_type_id].append(el)
                order.append(el.pk)

            for content_type in content_types.values():
                model = content_type.model_class()
                elements = content_types_elements[content_type.pk]
                pks = [element.pk for element in elements]

                for el in QuerySet(model).filter(pk__in=pks):
                    downcasts[el.pk] = el

            for pk in order:
                result.append(downcasts[pk])
            
            return result

    def _clone(self, *args, **kwargs):
        clone = super(PolymorphicQuerySet, self)._clone(*args, **kwargs)
        clone._downcast = self._downcast
        return clone
        
    def delete(self, *args, **kwargs):
        with PolymorphicOverride(False):
            super(PolymorphicQuerySet, self).delete(*args, **kwargs)

    def polymorphic(self, polymorphic=True):
        clone = self
        if polymorphic:
            clone = clone.prefetch_related('content_type')
        clone._downcast = polymorphic
        return clone

class PolymorphicManager(models.Manager):

    use_for_related_fields = True

    def __init__(self, cls=PolymorphicQuerySet, downcast=False):
        self._downcast = downcast
        self._cls = cls
        super(PolymorphicManager, self).__init__()
        
    def get_by_polymorphic_natural_key(self, *args):
        raise NotImplementedError()
        
    def get_by_natural_key(self, content_type, key):
        content_type = ContentType.objects.get_by_natural_key(*content_type)
        return content_type.model_class().objects.get_by_polymorphic_natural_key(*key)

    def get_query_set(self):
        qs = self._cls(self.model)
        if self._downcast:
            qs = qs.polymorphic()
        return qs

    def polymorphic(self, *args, **kwargs):
        return self.get_query_set().polymorphic(*args, **kwargs)
        

class PolymorphicModel(models.Model):

    content_type = models.ForeignKey(ContentType, editable=False)
    objects = PolymorphicManager()
    _downcasted = None

    @classmethod
    def get_admin_url(cls, content_type, object_id):
        if cls._meta.parents.keys():
            content_type = ContentType.objects.get_for_model(cls._meta.parents.keys()[-1])
        return "%s/%s/%s/" % (content_type.app_label, content_type.model, quote(object_id))

    def save(self, *args, **kwargs):
        if self.content_type_id is None:
            self.content_type = ContentType.objects.get_for_model(self.__class__)
        super(PolymorphicModel, self).save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        assert self._get_pk_val() is not None, "%s object can't be deleted because its %s attribute is set to None." % (self._meta.object_name, self._meta.pk.attname)
        with PolymorphicOverride(False):
            upcasted = self.__class__.objects.get(pk=self.pk)
            super(PolymorphicModel, upcasted).delete(*args, **kwargs)
    
    def downcast(self):
        if not self._downcasted:
            downcasted = self
            if not self.content_type_id is None:
                model = self.content_type.model_class()
                if(model != self.__class__):
                    try:
                        downcasted = model.objects.get(pk=self.pk)
                    except model.DoesNotExist:
                        raise Exception("Could not downcast to model class '{0}', lookup failed for pk '{1}'".format(model, self.pk))
            self._downcasted = downcasted    
        return self._downcasted
        
    def can_downcast(self):
        if not self.content_type_id is None:
            model = self.content_type.model_class()
            return model != self.__class__
        return False

    def resolve_content_type(self):
        if not self.content_type_id is None:
            return self.content_type
        else:
            return ContentType.objects.get_for_model(self.__class__)
            
    def polymorphic_natural_key(self):
        raise NotImplementedError()

    def natural_key(self):
        return (self.content_type.natural_key(), self.downcast().polymorphic_natural_key())
    
    class Meta:
        abstract = True