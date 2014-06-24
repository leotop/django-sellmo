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
from django.db.models.query import QuerySet
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.util import quote
from django.utils.functional import allow_lazy


def _polymorphic_descriptor(descriptor):
    class PolymorphicDescriptor(descriptor):
        def __get__(self, instance, instance_type=None):
            result = super(PolymorphicDescriptor, self) \
                .__get__(instance, instance_type)
            if getattr(result, 'pk', None) is not None:
                result = result.downcast()
            return result
    
    return PolymorphicDescriptor


class PolymorphicRelation(object):
    def contribute_to_class(self, cls, name, virtual_only=False):
        # Call original contribute_to_class
        super(PolymorphicRelation, self) \
            .contribute_to_class(cls, name, virtual_only)
        # Get descriptor class
        descriptor = getattr(cls, self.name).__class__
        # Overwrite with polymorphic desriptor
        setattr(cls, self.name, _polymorphic_descriptor(descriptor)(self))    
    

class PolymorphicForeignKey(PolymorphicRelation, models.ForeignKey):
    pass
    

class PolymorphicOneToOneField(PolymorphicRelation, models.OneToOneField):
    pass


class PolymorphicQuerySet(QuerySet):

    _downcast = False
    _can_downcast = True

    def __init__(self, *args, **kwargs):
        self._defered_calls = []
        if kwargs.has_key('downcast'):
            self._downcast = kwargs.pop('downcast')
        super(PolymorphicQuerySet, self).__init__(*args, **kwargs)
        
    def __apply_defered_calls__(self, queryset):
        for name, args, kwargs in self._defered_calls:
            queryset = getattr(queryset, name)(*args, **kwargs)
        return queryset
        
    def __defer__call__(self, name, args, kwargs, inheritable=False):
        if not inheritable and self._downcast:
            clone = self._clone()
            clone._defered_calls.append((name, args, kwargs))
        else:
            func = getattr(super(PolymorphicQuerySet, self), name)
            clone = func(*args, **kwargs)
            if inheritable: 
                clone._defered_calls.append((name, args, kwargs))
            else:
                clone._can_downcast = False
        return clone
    
    def iterator(self):
        if not self._downcast:
            return super(PolymorphicQuerySet, self).iterator()
        else:
            
            # Keep ordering and filter out all content types
            # Afterwards perform seperate queries for each content_type
            content_types = {}
            order = []
            bases = {}
            downcasts = {}
            out = []
            
            # Perform original query against ourselves so that we 
            # receive correct ordering and we can resolve only the 
            # content types needed for downcasting
            for obj in super(PolymorphicQuerySet, self).iterator():
                # Collect content type
                if not content_types.has_key(obj.content_type.pk):
                    content_types[obj.content_type.pk] = obj.content_type
                # Keep order
                bases[obj.pk] = obj
                order.append(obj.pk)

            # For each content type perform the actual query
            for content_type in content_types.values():
                model = content_type.model_class()
                # Make sure to filter at content_type even though we
                # query a subtyped model. We could still query models
                # which inherit from this subtype (A -> B -> C).
                qs = QuerySet(model).filter(content_type=content_type)
                # At this point apply defered query calls
                qs = self.__apply_defered_calls__(qs)
                for obj in qs:
                    base = bases[obj.pk]
                    base._downcasted = obj
                    obj.content_type = content_type
                    obj._downcasted_from = base
                    downcasts[obj.pk] = obj

            for pk in order:
                out.append(downcasts[pk])
            
            return out

    def _clone(self, *args, **kwargs):
        clone = super(PolymorphicQuerySet, self)._clone(*args, **kwargs)
        clone._downcast = self._downcast
        clone._can_downcast = self._can_downcast
        clone._defered_calls = list(self._defered_calls)
        return clone

    def polymorphic(self):
        if not self._can_downcast:
            raise Exception("Too late to downcast this queryset")
            
        clone = self._clone()
        if not self._downcast:
            clone = super(PolymorphicQuerySet, clone) \
                        .select_related('content_type')
            clone._downcast = True
        return clone
            
    def filter(self, *args, **kwargs):
        return self.__defer__call__('filter', args, kwargs, inheritable=True)
        
    def exclude(self, *args, **kwargs):
        return self.__defer__call__('exclude', args, kwargs, inheritable=True)
    
    def select_related(self, *args, **kwargs):
        return self.__defer__call__('select_related', args, kwargs)
        
    def only(self, *args, **kwargs):
        return self.__defer__call__('only', args, kwargs)
        
    def defer(self, *args, **kwargs):
        return self.__defer__call__('defer', args, kwargs)
        
    def annotate(self, *args, **kwargs):
        return self.__defer__call__('annotate', args, kwargs)
        
    def extra(self, *args, **kwargs):
        return self.__defer__call__('extra', args, kwargs)
        
    def using(self, *args, **kwargs):
        return self.__defer__call__('using', args, kwargs, inheritable=True)
    


class PolymorphicManager(models.Manager):

    use_for_related_fields = True

    def __init__(self, cls=PolymorphicQuerySet):
        self._cls = cls
        super(PolymorphicManager, self).__init__()

    def get_by_polymorphic_natural_key(self, *args):
        raise NotImplementedError()

    def get_by_natural_key(self, content_type, key):
        content_type = ContentType.objects.get_by_natural_key(*content_type)
        return content_type.model_class().objects \
                           .get_by_polymorphic_natural_key(*key)

    def get_queryset(self):
        return self._cls(self.model, using=self._db)

    def polymorphic(self, *args, **kwargs):
        return self.get_queryset().polymorphic(*args, **kwargs)


class PolymorphicModel(models.Model):

    content_type = models.ForeignKey(ContentType, editable=False)
    objects = PolymorphicManager()
    _downcasted = None
    _downcasted_from = None

    @classmethod
    def get_admin_url(cls, content_type, object_id):
        if cls._meta.parents.keys():
            content_type = ContentType.objects.get_for_model(
                cls._meta.parents.keys()[-1])
        return "{0}/{1}/{2}/".format(
            content_type.app_label,
            content_type.model,
            quote(object_id))

    def save(self, *args, **kwargs):
        if self.content_type_id is None:
            self.content_type = (ContentType.objects
                                 .get_for_model(self.__class__))
        super(PolymorphicModel, self).save(*args, **kwargs)

    def downcast(self):
        if not self._downcasted:
            downcasted = self
            if not self.content_type_id is None:
                model = self.content_type.model_class()
                if model is not self.__class__:
                    try:
                        downcasted = model.objects.get(pk=self.pk)
                    except model.DoesNotExist:
                        raise Exception(
                            "Could not downcast to model class '{0}', "
                            "lookup failed for pk '{1}'"
                            .format(model, self.pk))
            self._downcasted = downcasted
            self._downcasted._downcasted_from = self
        return self._downcasted

    def can_downcast(self):
        if not self.content_type_id is None:
            model = self.content_type.model_class()
            return model is not self.__class__
        return False

    def resolve_content_type(self):
        if not self.content_type_id is None:
            return self.content_type
        else:
            return ContentType.objects.get_for_model(self.__class__)

    def polymorphic_natural_key(self):
        raise NotImplementedError()

    def natural_key(self):
        return (self.content_type.natural_key(), 
                self.downcast().polymorphic_natural_key())

    class Meta:
        abstract = True
    
    
# South support

try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    pass
else:
    add_introspection_rules(
        [], 
        ["^sellmo\.core\.polymorphism\.PolymorphicForeignKey"])
    add_introspection_rules(
        [], 
        ["^sellmo\.core\.polymorphism\.PolymorphicOneToOneField"])

