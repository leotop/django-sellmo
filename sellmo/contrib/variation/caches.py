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
from sellmo.caching import Cache, cached
from sellmo.contrib.variation.signals import (variations_invalidating,
                                                      variations_invalidated)


from sellmo.core.query import PKIterator


class ProductVariationsCache(Cache):

    @staticmethod
    def materialize(cache, grouped=False):
        # Reconstruct
        if grouped:
            product_qs = modules.product.Product.objects.all().polymorphic()
            grouped_variations = []
            
            if len(cache) > 0:
                all_values = [variation['value'] for variation in cache]
                all_variants = [variation['variant'] for variation in cache]
                all_variants = list(PKIterator(product_qs, all_variants))
                attribute = modules.attribute.Attribute.objects \
                                   .get(pk=cache[0]['attribute'])
                
                model = attribute.get_type().get_model()
                if model:
                    all_values = list(PKIterator(model, all_values))
            
            for variation in cache:
                
                # Construct variations query
                variations = modules.variation.Variations.objects.all()
                variations.query = variation['variations']
                
                # Get our slice
                value = all_values[0]
                all_values = all_values[1:]
                variant = all_variants[0]
                all_variants = all_variants[1:]
                
                grouped_variations.append({
                    'attribute': attribute,
                    'value': value,
                    'variations': variations,
                    'variant': variant,
                })

            variations = grouped_variations
        else:
            variations = modules.variation.Variations.objects.all()
            variations.query = cache

        return variations

    def on_variations_invalidated(self, sender, product, **kwargs):
        keys = [
            self.get_variations_key(product.pk, grouped=True),
            self.get_variations_key(product.pk, grouped=False)
        ]
        self.delete(*keys)

    def get_variations_key(self, product_pk, grouped=False):
        if not grouped:
            return 'product_{0}_variations'.format(product_pk)
        else:
            return 'product_{0}_grouped_variations'.format(product_pk)

    def capture(self, product, grouped=False, **kwargs):
        variations = self.get(self.get_variations_key(product.pk, grouped))
        variations_hit = variations is not None
        if variations_hit:
            try:
                variations = self.materialize(variations, grouped)
            except Exception:
                # Cache must have been invalid, clear it.
                self.delete(self.get_variations_key(product.pk, grouped))
                variations = None
                variations_hit = False
        
        return {
            'variations': variations,
            'variations_hit': variations_hit
        }

    def finalize(self, product, variations, variations_hit, grouped=False,
                 **kwargs):
        if not variations_hit:
            if grouped:
                cache = []
                for variation in variations:
                    attribute = variation['attribute']
                    value = variation['value']
                    if attribute.get_type().get_model():
                        value = value.pk
                    cache.append({
                        'attribute': attribute.pk,
                        'value': value,
                        'variations': variation['variations'].query,
                        'variant': variation['variant'].pk,
                    })
            else:
                cache = variations.query

            self.set(self.get_variations_key(product.pk, grouped), cache)

    def hookup(self):
        variations_invalidated.connect(self.on_variations_invalidated)


class VariationChoiceCache(Cache):

    def on_variations_invalidating(self, sender, product, **kwargs):
        product = product.downcast()
        keys = [
            self.get_choice_key(variation.pk) for variation in
            product.variations.all()
        ]
        self.delete(*keys)

    def get_choice_key(self, pk):
        return 'variation_{0}_choice'.format(pk)

    def capture(self, variation, choice=None, **kwargs):
        choice = self.get(self.get_choice_key(variation.pk))
        return {
            'choice': choice,
            'choice_hit': choice is not None
        }

    def finalize(self, variation, choice, choice_hit, **kwargs):
        if not choice_hit:
            self.set(self.get_choice_key(variation.pk), choice)

    def hookup(self):
        variations_invalidating.connect(self.on_variations_invalidating)


get_variations = cached(
    ProductVariationsCache, 'get_variations', 'variation', timeout=None)
generate_variation_choice = cached(
    VariationChoiceCache, 'generate_variation_choice', 'variation', timeout=None)
