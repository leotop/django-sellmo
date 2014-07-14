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
from sellmo.contrib.polymorphism.admin import PolymorphicParentModelAdmin

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _


class ShippingMethodAdminBase(admin.ModelAdmin):
    pass


class ShippingMethodParentAdmin(PolymorphicParentModelAdmin):
    base_model = modules.shipping.ShippingMethod
    child_models = []

    polymorphic_list = True
    list_display = ['name']
    list_display_links = ['name']
    search_fields = ['name']


class ShippingCarrierAdmin(admin.ModelAdmin):
    pass


admin.site.register(modules.shipping.ShippingMethod, ShippingMethodParentAdmin)
admin.site.register(modules.shipping.ShippingCarrier, ShippingCarrierAdmin)