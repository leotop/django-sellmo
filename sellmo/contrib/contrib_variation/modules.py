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
from sellmo.api.pricing import Price
from sellmo.utils.formatting import call_or_format
from sellmo.contrib.contrib_variation.models import Variant, Variation, VariationsState
from sellmo.contrib.contrib_attribute.query import ProductQ

from django.http import Http404
from django.utils.translation import ugettext_lazy as _

#

from django.db.models import Q

#

from sellmo.contrib.contrib_variation.config import settings

#

class VariationModule(Module):

    namespace = 'variation'
    batch_buy_enabled = False
    Variant = Variant
    Variation = Variation
    VariationsState = VariationsState
    product_subtypes = []
    subtypes = []
        
    @classmethod
    def register_product_subtype(self, subtype):
        self.product_subtypes.append(subtype)
    
    @chainable()
    def get_variations(self, chain, product, grouped=False, variations=None, **kwargs):
        if variations is None:
            variations = modules.variation.Variation.objects.for_product(product)
            if grouped:
                attributes = modules.attribute.Attribute.objects.which_variate(product=product)
                group = attributes.filter(groups=True).first()
                if group:
                    result = []
                    values = modules.attribute.Value.objects.which_variate(product).for_attribute(attribute=group, distinct=True)
                    values = modules.attribute.get_sorted_values(values=values, attribute=group)
                    for value in values:
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
                        result += [{
                            'attribute' : group,
                            'value' : value,
                            'variations' : variations,
                            'variant' : variations[0].group_variant.downcast(),
                        }]
                    variations = result
                else:
                    return None
        
        if chain:
            out = chain.execute(product=product, grouped=grouped, variations=variations, **kwargs)
            if out.has_key('variations'):
                variations = out['variations']
        
        return variations
    
    @chainable()
    def get_variation_choice(self, chain, variation, choice=None, **kwargs):   
        if choice is None:
            choice = self.generate_variation_choice(variation=variation, choice=choice)
        
        if chain:
             out = chain.execute(variation=variation, choice=choice, **kwargs)
             if out.has_key('choice'):
                 choice = out['choice']
                 
        return choice
        
    @chainable()
    def generate_variation_choice(self, chain, variation, choice=None, **kwargs):
        if choice is None:
            variant = variation.variant.downcast()
            price_adjustment = None
            if hasattr(variant, '_is_variant') and variant.price_adjustment:
                price_adjustment = Price(variant.price_adjustment)
            
            values = settings.VARIATION_VALUE_SEPERATOR.join(
                [unicode(value) for value in variation.values.all().order_by('attribute')]
            )
            
            choice = call_or_format(settings.VARIATION_CHOICE_FORMAT,
                variation=variation,
                variant=variant,
                values=values,
                price_adjustment=price_adjustment
            )
        
        if chain:
            out = chain.execute(variation=variation, choice=choice, **kwargs)
            if out.has_key('choice'):
                choice = out['choice']
        return choice
        
    @chainable()
    def generate_variation_description(self, chain, product, values, description=None, **kwargs):
        if description is None:
            
            values = settings.VARIATION_VALUE_SEPERATOR.join(
                [unicode(value) for value in values]
            )
            
            description = call_or_format(settings.VARIATION_DESCRIPTION_FORMAT,
                product=product,
                values=values
            )
            
        if chain:
            out = chain.execute(product=product, values=values, description=description, **kwargs)
            if out.has_key('description'):
                description = out['description']
        
        return description
    
        