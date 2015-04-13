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


from sellmo import modules
from sellmo.utils.forms import FormFactory

from django import forms
from django.utils.translation import ugettext_lazy as _


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
                self.__attribute_field_names[attribute.key]: 
                instance.attributes[attribute.key]
                for attribute in self.__attributes
            })
        kwargs['initial'] = initial
        super(ProductAttributeFormMixin, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(ProductAttributeFormMixin, self).save(commit=False)
        for attribute in self.__attributes:
            value = self.cleaned_data.get(
                self.__attribute_field_names[attribute.key])
            instance.attributes[attribute.key] = value
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ProductAttributeFormFactory(FormFactory):
        
    def __init__(self, form=forms.ModelForm, mixin=ProductAttributeFormMixin, 
                 prefix=None):
        self.form = form
        self.mixin = mixin
        self.prefix = prefix

    def get_attributes(self):
        return modules.attribute.Attribute.objects.all()

    def get_attribute_formfield(self, attribute):
        args = []
        kwargs = {
            'label': attribute.name,
            'required': attribute.required
        }
        
        formfield = attribute.get_type().get_formfield_type()
        if formfield is forms.ModelChoiceField:
            args = [attribute.get_type().get_model().objects.all()]
        
        return formfield(*args, **kwargs)

    def factory(self):
        attributes = self.get_attributes()
        names = {}
        fields = {}
        attr_dict = {
            '_{0}__attributes'.format(self.mixin.__name__): attributes,
            '_{0}__attribute_field_names'.format(self.mixin.__name__): names,
            '_{0}__attribute_fields'.format(self.mixin.__name__): fields,
        }
        for attribute in attributes:
            field = self.get_attribute_formfield(attribute)
            name = attribute.key
            if self.prefix:
                name = '{0}_{1}'.format(self.prefix, name)
            names[attribute.key] = name
            fields[attribute.key] = field
            attr_dict[name] = field

        return type('ProductAttributeForm', (self.mixin, self.form), attr_dict)
