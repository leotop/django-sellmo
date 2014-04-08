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
from sellmo.caching import Cache, cached
from sellmo.utils.querying import list_from_pks
from sellmo.contrib.contrib_variation.signals import (variations_deprecating,
                                                      variations_invalidated)


class ProductVariationsCache(Cache):

    @staticmethod
    def materialize(cache, grouped=False):
        # Collect all variations so we can do one big query
        if not grouped:
            all_variations = list(cache)
        else:
            all_variations = []
            for el in cache:
                all_variations += el['variations']

        # Query them all
        all_variations = list_from_pks(
            modules.variation.Variation.objects.filter(pk__in=all_variations),
            all_variations)

        # Reconstruct
        if grouped:
            grouped_variations = []
            if len(cache) > 0:
                all_values = [variation['value'] for variation in cache]
                all_values = list_from_pks(
                    modules.attribute.Value.objects.filter(pk__in=all_values),
                    all_values)
                all_variants = [variation['variant'] for variation in cache]
                all_variants = list_from_pks(
                    modules.product.Product.objects.polymorphic().filter(
                        pk__in=all_variants), 
                    all_variants)
                attribute = modules.attribute.Attribute.objects.get(
                    pk=cache[0]['attribute'])

            for variation in cache:

                # Get our slice
                variations = all_variations[:len(variation['variations'])]
                all_variations = all_variations[len(variations):]
                value = all_values[0]
                all_values = all_values[1:]
                variant = all_variants[0]
                all_variants = all_variants[1:]

                grouped_variations += [{
                    'attribute': attribute,
                    'value': value,
                    'variations': variations,
                    'variant': variant,
                }]

            variations = grouped_variations
        else:
            variations = all_variations

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
            cache = []
            for variation in variations:
                if not grouped:
                    cache.append(variation.key)
                else:
                    cache.append({
                        'attribute': variation['attribute'].pk,
                        'value': variation['value'].pk,
                        'variations': [el.pk for el in 
                            variation['variations']],
                        'variant': variation['variant'].pk,
                    })

            self.set(self.get_variations_key(product.pk, grouped), cache)

    def hookup(self):
        variations_invalidated.connect(self.on_variations_invalidated)


class VariationChoiceCache(Cache):

    def on_variations_deprecating(self, sender, product, **kwargs):
        product = product.downcast()
        keys = [
            self.get_choice_key(variation.pk) for variation in
            product.get_variations(invalidated=True)
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
        variations_deprecating.connect(self.on_variations_deprecating)


get_variations = cached(
    ProductVariationsCache, 'get_variations', 'variation', timeout=None)
get_variation_choice = cached(
    VariationChoiceCache, 'get_variation_choice', 'variation', timeout=None)
