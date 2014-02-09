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

#

from sellmo import modules

#

from django import forms
from django.forms import ValidationError
from django.forms.models import ModelForm, BaseInlineFormSet
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst
from django.utils import six
from django.contrib.admin.sites import NotRegistered
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.contrib.contenttypes.models import ContentType

#

class ProductAttributeFormMixin(object):
    
    def __init__(self, *args, **kwargs):
        initial = {}
        if 'initial' in kwargs:
            initial = kwargs['initial']
        instance = None
        if 'instance' in kwargs:
            instance = kwargs['instance']
        if instance:
            initial.update({
                self.__attribute_field_names[attribute.key] : instance.attributes[attribute.key] 
                for attribute in self.__attributes
            })
        kwargs['initial'] = initial
        super(ProductAttributeFormMixin, self).__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super(ProductAttributeFormMixin, self).save(commit=False)
        for attribute in self.__attributes:
            value = self.cleaned_data.get(self.__attribute_field_names[attribute.key])
            instance.attributes[attribute.key] = value
        if commit:
            instance.save()
        return instance

class ProductAttributeFormFactory(object):
    
    FIELD_CLASSES = {
        modules.attribute.Attribute.TYPE_STRING : forms.CharField,
        modules.attribute.Attribute.TYPE_INT : forms.IntegerField,
        modules.attribute.Attribute.TYPE_FLOAT : forms.FloatField,
        modules.attribute.Attribute.TYPE_OBJECT : forms.ModelChoiceField,
    }
    
    def __init__(self, form=forms.ModelForm, mixin=ProductAttributeFormMixin, prefix=None):
        self.form = form
        self.mixin = mixin
        self.prefix = prefix
        
    def get_attributes(self):
        return modules.attribute.Attribute.objects.all()
        
    def get_attribute_field(self, attribute):
        field = self.FIELD_CLASSES[attribute.type]
        field = field(
            *self.get_attribute_field_args(attribute, field),
            **self.get_attribute_field_kwargs(attribute, field)
        )
        
        return field
        
    def get_attribute_field_kwargs(self, attribute, field):
        kwargs = {
            'label' : attribute.label,
            'required' : attribute.required,
            'help_text' : attribute.help_text,
            'validators' : attribute.validators,
        }
        
        return kwargs
        
    def get_attribute_field_args(self, attribute, field):
        args = []
        if field is forms.ModelChoiceField:
            args.append(attribute.get_object_choices())
        
        return args
        
    def factory(self):
        attributes = self.get_attributes()
        names = {}
        fields = {}
        attr_dict = {
            '_{0}__attributes'.format(self.mixin.__name__) : attributes,
            '_{0}__attribute_field_names'.format(self.mixin.__name__) : names,
            '_{0}__attribute_fields'.format(self.mixin.__name__) : fields,
        }
        for attribute in attributes:
            field = self.get_attribute_field(attribute)
            name = attribute.key
            if self.prefix:
                name = '{0}_{1}'.format(self.prefix, name)
            names[attribute.key] = name
            fields[attribute.key] = field
            attr_dict[name] = field
        
        return type('ProductAttributeForm', (self.mixin, self.form), attr_dict)
        
    def __get__(self, obj, objtype):
        return self.factory()