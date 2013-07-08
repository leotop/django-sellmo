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
from sellmo.api.decorators import load
from sellmo.api.pricing import Price

#

from django.db import models

#

@load(after='load_pricing_Stampable', before='finalize_pricing_Stampable')
def load_model():
    modules.pricing.Stampable.add_to_class('amount', modules.pricing.construct_decimal_field(default=0))
    for type in modules.pricing.types:
        modules.pricing.Stampable.add_to_class('%s_amount' % type, modules.pricing.construct_decimal_field(default=0))

class Stampable(models.Model):
    
    @staticmethod
    def get_stampable_fields():
        return ['amount'] + ['%s_amount' % type for type in modules.pricing.types]
    
    def get_price(self, **kwargs):
        """
        Reconstructs the stamped price 
        """
        return modules.pricing.retrieve(stampable=self, **kwargs)
        
    def set_price(self, value, **kwargs):
        """
        Stamps the price 
        """
        modules.pricing.stamp(stampable=self, price=value, **kwargs)
        
    """
    Enabled suptypes to store(stamp) a price and retrieve this exact same price
    """
    price = property(get_price, set_price)
    
    class Meta:
        abstract = True