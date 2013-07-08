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
from sellmo.api.decorators import load
from sellmo.magic import ModelMixin

#

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

#

# Make sure to load directly after finalize_tax_Tax and thus 
# directly after finalize_product_Product
@load(after='finalize_tax_Tax', directly=True)
def load_model():
    class ProductMixin(ModelMixin):
        model = modules.product.Product
        tax = models.ForeignKey(
            modules.tax.Tax,
            blank = True,
            null = True,
            related_name = 'products',
            verbose_name = _("tax"),
        )

# Make sure to load directly after finalize_product_ProductRelatable and thus 
# directly after finalize_product_Product          
@load(action='finalize_tax_Tax', after='finalize_product_ProductRelatable', directly=True)
def finalize_model():
    class Tax(modules.tax.Tax, modules.product.ProductRelatable):
        
        @classmethod
        def get_for_product_query(cls, product):
            return super(Tax, cls).get_for_product_query(product) | Q(products=product)
            
        @classmethod
        def get_best_for_product(cls, product, matches):
            better = matches.filter(products=product)
            if better:
                matches = better
            matches = matches.order_by('-rate')
            return super(Tax, cls).get_best_for_product(product=product, matches=matches)
        
        class Meta:
            app_label = 'tax'
            verbose_name = _("tax")
            verbose_name_plural = _("taxes")
    
    modules.tax.Tax = Tax
        
class Tax(models.Model):
    
    name = models.CharField(
        max_length = 20,
        verbose_name = _("name"),
    )
    
    rate = modules.pricing.construct_decimal_field(
        verbose_name = _("rate"),
    )
    
    class Meta:
        abstract = True
    
    def __unicode__(self):
        return self.name
        
# Init modules
from sellmo.contrib.contrib_tax.modules import *
            