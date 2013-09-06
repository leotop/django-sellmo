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

from sellmo import modules
from sellmo.contrib.contrib_variation.utils import is_unique_slug

#

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_text
from django.utils.text import capfirst

# Exceptions

class ProductUnassignedException(Exception):
    pass
    
class DuplicateSlugException(Exception):
    pass
    
#

def get_differs_field_name(name):
    return '%s_differs' % name

class VariantMixin(object):
    
    non_variable_fields = ['content_type', 'slug', 'product']
    non_variable_field_types = [models.BooleanField]
    _is_variant = True
    
    @classmethod
    def get_variable_fields(cls):
        fields = cls._meta.many_to_many + cls._meta.fields
        for field in fields:
            if not field.auto_created and not field.name in cls.non_variable_fields and not field.__class__ in cls.non_variable_field_types:
                yield field
    
    def get_product(self):
        if hasattr(self, 'product_id') and self.product_id != None:
            return self.product     
        return None
        
    def validate_unique(self, exclude=None):
        super(self.__class__.__base__, self).validate_unique(exclude)
        if 'slug' not in exclude:
            if not is_unique_slug(self.slug, ignore=self):
                message = _("%(model_name)s with this %(field_label)s already exists.") % {
                    'model_name': capfirst(modules.product.Product._meta.verbose_name),
                    'field_label': 'slug'
                }
                raise ValidationError({'slug' : [message]})     

    def save(self, *args, **kwargs):
        product = self.get_product()
        if not product:
            raise ProductUnassignedException()
            
        # See if object is newly created
        try:
            exists = not self.pk is None
        except Exception:
            exists = False
            
        def assign_field(field, val, product_val):
            differs = getattr(self, get_differs_field_name(field.name))
            
            # Empty field will always copy it's parent field
            if not val:
                val = product_val
                differs = False
               
            if not exists and val != product_val:
                # Newly created and we already differ
                differs = True
               
            # See if we need to copy our parent's field
            if not differs and val != product_val:
                val = product_val
            
            setattr(self, field.name, val)
            setattr(self, get_differs_field_name(field.name), differs)
                
        
        for field in self.__class__.get_variable_fields():
            # Handle all fields except many to many
            if isinstance(field, models.ManyToManyField):
                continue
            
            val = getattr(self, field.name)
            product_val = getattr(product, field.name)
            assign_field(field, val, product_val)
                
        super(VariantMixin, self).save(*args, **kwargs)
        
        for field in self.__class__.get_variable_fields():
            # Handle many to many 
            if not isinstance(field, models.ManyToManyField):
                continue
            
            val = getattr(self, field.name)
            product_val = getattr(product, field.name)
            val = list(val.all())
            product_val = list(product_val.all())
            assign_field(field, val, product_val)
            

    class Meta:
        app_label = 'product'
        verbose_name = _("variant")
        verbose_name_plural = _("variants")
        
class VariantFieldDescriptor(object):

    def __init__(self, field, descriptor=None):
        self.field = field
        self.descriptor = descriptor

    def __get__(self, obj, objtype):
        if not self.descriptor:
            return obj.__dict__.get(self.field.name, None)
        else:
            return self.descriptor.__get__(obj, objtype)

    def __set__(self, obj, val):
        
        # See if object is newly created
        try:
            exists = not obj.pk is None
        except Exception:
            exists = False
        
        if exists:
            # See if we differ and keep track
            differs = getattr(obj, get_differs_field_name(self.field.name), False)
            if not differs:
                try:
                    # In case we are initializing, an exception could occur while
                    # getting this field's value
                    old_val = getattr(obj, self.field.name)
                except Exception:
                    pass
                else:
                    differs = not old_val is None and old_val != val
                    setattr(obj, get_differs_field_name(self.field.name), differs)
        
        # Now set
        if not self.descriptor:
            obj.__dict__[self.field.name] = val
        else:
            self.descriptor.__set__(obj, val)
            
        
            