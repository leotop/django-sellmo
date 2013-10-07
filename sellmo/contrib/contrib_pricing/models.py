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

from decimal import Decimal

#

from sellmo import modules
from sellmo.api.decorators import load

#

from django.db import models
from django.utils.translation import ugettext_lazy as _

#

@load(action='finalize_qty_pricing_ProductQtyPrice', after='finalize_product_Product')
def finalize_model():
    class ProductQtyPrice(modules.qty_pricing.ProductQtyPrice):
        product = models.ForeignKey(
            modules.product.Product,
            related_name = 'qty_prices',
            verbose_name = _("product"),
        )

        class Meta:
            app_label = 'pricing'
            verbose_name = _("qty price")
            verbose_name_plural = _("qty prices")

    modules.qty_pricing.ProductQtyPrice = ProductQtyPrice

class QtyPriceBase(models.Model):
    
    qty = models.PositiveIntegerField(
        verbose_name = _("quantity"),
        default = 1,
    )
    
    def __unicode__(self):
        return _("%s qty or more") % unicode(self.qty)
    
    class Meta:
        abstract = True


class QtyPrice(QtyPriceBase):
    
    amount = modules.pricing.construct_decimal_field(
        verbose_name = _("amount"),
    )
    
    class Meta:
        abstract = True
        
class QtyPriceRatio(QtyPriceBase):
    
    ratio = modules.pricing.construct_decimal_field(
        default = Decimal('1.00'),
        verbose_name = _("ratio"),
    )
    
    class Meta:
        abstract = True

class ProductQtyPrice(QtyPrice):
    
    class Meta:
        abstract = True
        
# Init modules
from sellmo.contrib.contrib_pricing.modules import *