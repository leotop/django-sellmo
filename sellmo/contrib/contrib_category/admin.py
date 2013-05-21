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
from sellmo.contrib.contrib_category.models import Category

#

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.sites import NotRegistered

#

class ProductCategoryMixin(object):
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            kwargs['queryset'] = modules.category.Category.objects.all().prefetch_related('parent')
        return super(ProductCategoryMixin, self).formfield_for_manytomany(db_field, request, **kwargs)

class ProductCategoryListFilter(admin.SimpleListFilter):
    title = _("category")
    parameter_name = 'category'
    
    def lookups(self, request, model_admin):
        return [(str(category.pk), unicode(category)) for category in modules.category.Category.objects.all()]
        
    def queryset(self, request, queryset):
        pk = self.value()
        if pk != None:
            category = modules.category.Category.objects.get(pk=pk)
            return queryset.in_category(category)
        else:
            return queryset.all()
            
class CategoryParentListFilter(admin.SimpleListFilter):
    title = _("parent category")
    parameter_name = 'parent'
    
    def lookups(self, request, model_admin):
        return [(str(category.pk), unicode(category)) for category in modules.category.Category.objects.all()]
        
    def queryset(self, request, queryset):
        pk = self.value()
        if pk != None:
            category = modules.category.Category.objects.get(pk=pk)
            return queryset.in_parent(category)
        else:
            return queryset.all()