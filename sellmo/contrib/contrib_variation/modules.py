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

from sellmo import modules, Module
from sellmo.api.decorators import view, chainable
from sellmo.contrib.contrib_variation.models import Variation, VariationRecipe
from sellmo.contrib.contrib_attribute.query import ProductQ

from django.http import Http404
from django.utils.translation import ugettext_lazy as _

#

from django.db.models import Q

#

class VariationModule(Module):

    namespace = 'variation'
    batch_buy_enabled = False
    Variation = Variation
    VariationRecipe = VariationRecipe
    
    def __init__(self):
        self.product_subtypes = []
        self.subtypes = []
        
    def register_product_subtype(self, subtype):
        self.product_subtypes.append(subtype)
    
    @chainable()
    def get_variations(self, chain, product, grouped=False, **kwargs):
        variations = modules.variation.Variation.objects.for_product(product)
        
        if grouped:
            attributes = modules.attribute.Attribute.objects.which_variates(product=product)
            
            try:
                group = attributes.get(groups=True)
            except modules.attribute.Attribute.DoesNotExist:
                return None
            else:
                result = ()
                for value in modules.attribute.Value.objects.for_product_or_variant(product).for_attribute(attribute=group, distinct=True):
                    
                    # Get variations for this grouped attribute / value combination
                    qargs = {
                        'values__attribute' : group,
                        'values__%s' % group.value_field : value.get_value(),
                        'product' : product,
                    }
                    
                    variations = modules.variation.Variation.objects.filter(**qargs)
                    if not variations:
                        continue
                    
                    # Build grouped result
                    result += ({
                        'attribute' : group,
                        'value' : value,
                        'variations' : variations,
                        'variant' : variations[0].group_variant,
                    },)
                variations = result
        
        return variations
        
    @chainable()
    def get_variation_choice(self, chain, variation, choice=None, **kwargs):
        if choice is None:
            choice = u", ".join([u"%s: %s" % (value.attribute.name ,unicode(value.value)) for value in variation.values.all().order_by('attribute')])
            
        if chain:
            out = chain.execute(variation=variation, choice=choice, **kwargs)
            if out.has_key('choice'):
                choice = out['choice']
                
        return choice
        
    @chainable()
    def generate_variation_description(self, chain, product, values, description=None, **kwargs):
        if description is None:
            if hasattr(product, 'product'):
                product = product.product
            prefix = unicode(product)
            description = u"%s %s" % (prefix, u", ".join([unicode(value.value) for value in values]))
            
        if chain:
            out = chain.execute(product=product, values=values, description=description, **kwargs)
            if out.has_key('description'):
                description = out['description']
        
        return description