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


from django.db.models.signals import post_save, post_delete

from sellmo import modules
from sellmo.api.decorators import load
from sellmo.api import indexing


@load(before='finalize_product_ProductIndex')
def load_index():
    class ProductIndex(modules.product.ProductIndex):
    
        def get_fields(self):
            fields = super(ProductIndex, self).get_fields()
            for attribute in modules.attribute.Attribute.objects.all():
                fields['%s_attr' % attribute.key] = None
            return fields
    
    modules.product.ProductIndex = ProductIndex


def on_value_post_save(sender, instance, raw=False, update_fields=None,
                       **kwargs):
    if not raw:
        index = modules.indexing.get_index('product')
        index.update(product=instance.product)


def on_value_post_delete(sender, instance, raw=False, update_fields=None,
                       **kwargs):
    if not raw:
        index = modules.indexing.get_index('product')
        index.update(product=instance.product)


def on_attribute_post_save(sender, instance, raw=False, update_fields=None,
                       **kwargs):
    if not raw:
        modules.indexing.invalidate_index('product')


def on_attribute_post_delete(sender, instance, raw=False, update_fields=None,
                       **kwargs):
    if not raw:
        modules.indexing.invalidate_index('product')


post_save.connect(on_value_post_save, sender=modules.attribute.Value)    
post_save.connect(on_value_post_delete, sender=modules.attribute.Value)
post_save.connect(on_attribute_post_save, sender=modules.attribute.Attribute)    
post_save.connect(on_attribute_post_delete, sender=modules.attribute.Attribute)