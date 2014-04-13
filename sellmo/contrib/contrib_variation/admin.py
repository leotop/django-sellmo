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
from sellmo.contrib.contrib_variation \
           .forms import (VariantAttributeFormMixin, 
                          ProductVariationFormFactory,
                          ProductVariationFormMixin)                                             
from sellmo.contrib.contrib_attribute \
           .admin import ProductAttributeMixin
from sellmo.contrib.contrib_attribute \
           .forms import ProductAttributeFormFactory

from django import forms
from django.forms import ValidationError
from django.forms.models import ModelForm
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst
from django.utils import six
from django.contrib.admin.sites import NotRegistered
from django.contrib.contenttypes.models import ContentType


class VariantAttributeMixin(ProductAttributeMixin):
    form = ProductAttributeFormFactory(
        mixin=VariantAttributeFormMixin, prefix='attribute')


class ProductVariationMixin(object):

    form = ProductVariationFormFactory(
        mixin=ProductVariationFormMixin, prefix='variations')

    def save_model(self, request, obj, form, change):
        obj.save()
        form.save_variations()

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(
            ProductVariationMixin, self).get_fieldsets(request, obj)
        fields = [
            'variations_{0}'.format(key) for key in 
            modules.attribute.Attribute.objects.filter(variates=True)
                                               .values_list('key', flat=True)
        ]
        fieldsets += ((_("Variations"), {'fields': fields}),)
        return fieldsets


class VariationAdmin(admin.ModelAdmin):
    pass


admin.site.register(modules.variation.Variation, VariationAdmin)
