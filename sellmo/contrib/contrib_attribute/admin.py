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
from sellmo.contrib.contrib_attribute.forms import ProductAttributeForm
from sellmo.contrib.contrib_attribute.models import ValueObject

#

from django import forms
from django.forms import ValidationError
from django.forms.models import ModelForm, BaseInlineFormSet
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst
from django.utils import six
from django.contrib.admin.sites import NotRegistered
from django.contrib.contenttypes.models import ContentType

#
            
class ProductAttributeMixin(object):
    
    form = ProductAttributeForm
    
    def get_fieldsets(self, request, obj=None):
    
        fieldsets = ()
        if self.declared_fieldsets:
            fieldsets = self.declared_fieldsets
        
        fieldsets += ((_("Attributes"), {'fields': modules.attribute.Attribute.objects.values_list('key', flat=True)}),)
        return fieldsets
    
        
#

class AttributeAdmin(admin.ModelAdmin):
    
    list_display = ['name', 'required']
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'object_choices':
            kwargs['queryset'] = ValueObject.objects.polymorphic().all()
        return super(AttributeAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

class ValueAdmin(admin.ModelAdmin):
    
    list_display = ['product', 'attribute', 'value']
    
    def value(self, obj):
        return obj.get_value()

admin.site.register(modules.attribute.Attribute, AttributeAdmin)
admin.site.register(modules.attribute.Value, ValueAdmin)

