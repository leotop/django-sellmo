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


from sellmo import modules, Module
from sellmo.api.decorators import view, chainable
from sellmo.api.pricing import Price
from sellmo.api.configuration import define_setting
from sellmo.utils.formatting import call_or_format
from sellmo.contrib.contrib_variation.models import (Variant,
                                                     Variation,
                                                     VariationsState,
                                                     VariationPurchase)
from sellmo.contrib.contrib_attribute.query import product_q

from django.http import Http404
from django.utils.translation import ugettext_lazy as _

from django.db.models import Q
from django.db.models.signals import post_save, m2m_changed


def choice_format(values, price_adjustment, **kwargs):
    if price_adjustment:
        if price_adjustment.amount > 0:
            return (
                u"{values} +{price_adjustment}"
                .format(values=values, price_adjustment=price_adjustment))
        else:
            return (
                u"{values} -{price_adjustment}"
                .format(values=values, price_adjustment=-price_adjustment))
    return u"{values}".format(values=values)


class VariationModule(Module):

    namespace = 'variation'
    batch_buy_enabled = False
    Variant = Variant
    Variation = Variation
    VariationsState = VariationsState
    VariationPurchase = VariationPurchase
    product_subtypes = []
    subtypes = []
    m2m_relations = {}
    
    variation_choice_format = define_setting(
        'VARIATION_CHOICE_FORMAT',
        default=choice_format)
    
    variation_description_format = define_setting(
        'VARIATION_DESCRIPTION_FORMAT',
        default=u"{prefix} ({values})")
    
    variation_value_seperator = define_setting(
        'VARIATION_VALUE_SEPERATOR',
        default=u", ")

    def __init__(self, *args, **kwargs):
        for field, reverse in self.m2m_relations.values():
            m2m_changed.connect(self.on_m2m_changed, sender=field.rel.through)
        for subtype in self.subtypes:
            post_save.connect(self.on_variant_post_save, sender=subtype)

    def on_m2m_changed(self, sender, instance, action, reverse, pk_set,
                       **kwargs):
        if action in ('pre_clear', 'pre_remove', 'post_add'):
            field, field_reverse = self.m2m_relations[str(sender)]
            relation = field.name
            products = [instance]
            action = action.split('_')[1]

            if (reverse ^ field_reverse):
                if field_reverse:
                    products = list(getattr(instance, field.name).all())
                    relation = field.rel.related_name
                else:
                    products = list(
                        getattr(instance, field.rel.related_name).all())
                pk_set = set([instance.pk])
                if action == 'clear':
                    action = 'remove'

            elif reverse and field_reverse:
                relation = field.rel.related_name

            for product in products:
                downcasted = product.downcast()
                if not getattr(downcasted, '_is_variant', False):
                    for variant in downcasted.variants.all():
                        m2m = getattr(variant, relation)
                        if action == 'clear':
                            m2m.clear()
                        elif action == 'remove':
                            m2m.remove(*pk_set)
                        elif action == 'add':
                            m2m.add(*pk_set)

    def on_variant_post_save(self, sender, instance, created, raw=False,
                             **kwargs):
        if not raw and created:
            for field, reverse in self.m2m_relations.values():
                relation = (field.name if not reverse else 
                            field.rel.related_name)
                relation = (field.name if not reverse else
                            field.rel.related_name)
                getattr(instance, relation).add(
                    *list(getattr(instance.product, relation).all()))
                instance.save()

    @classmethod
    def register_product_subtype(self, subtype):
        self.product_subtypes.append(subtype)

    @classmethod
    def mirror_m2m_field(self, field, reverse):
        if str(field.rel.through) not in self.m2m_relations:
            self.m2m_relations[str(field.rel.through)] = (field, reverse)

    @chainable()
    def get_variations(self, chain, product, grouped=False, variations=None,
                       **kwargs):
        if variations is None:
            variations = modules.variation.Variation \
                                .objects.for_product(product)
            if grouped:
                attributes = modules.attribute.Attribute.objects \
                                    .which_variate(product=product)
                group = attributes.filter(groups=True).first()
                if group:
                    result = []
                    
                    values = (modules.attribute.Value.objects
                                .which_variate(product)
                                .for_attribute(group)
                                .attribute_values()
                                .distinct())
                    values = (modules.attribute
                                .get_sorted_values(values=values,
                                                    attribute=group))
                    
                    for value in values:
                        # Get variations for this grouped attribute / value
                        # combination
                        qargs = {
                            'values__attribute': group,
                            'values__{0}'.format(group.value_field): 
                                value,
                            'product': product,
                        }

                        variations = modules.variation.Variation.objects \
                                            .filter(**qargs)
                        if not variations:
                            continue

                        # Build grouped result
                        result += [{
                            'attribute': group,
                            'value': value,
                            'variations': variations,
                            'variant': variations[0].group_variant.downcast(),
                        }]
                    variations = result
                else:
                    return None
        
        if chain:
            out = chain.execute(
                product=product, grouped=grouped,
                variations=variations, **kwargs)
            if out.has_key('variations'):
                variations = out['variations']

        return variations

    @chainable()
    def get_variation_choice(self, chain, variation, choice=None, **kwargs):
        if choice is None:
            choice = self.generate_variation_choice(
                variation=variation, choice=choice)

        if chain:
            out = chain.execute(variation=variation, choice=choice, **kwargs)
            if out.has_key('choice'):
                choice = out['choice']

        return choice

    @chainable()
    def generate_variation_choice(self, chain, variation, choice=None,
                                  **kwargs):
        if choice is None:
            variant = variation.variant.downcast()
            price_adjustment = None
            
            if hasattr(variant, '_is_variant'):
                price_adjustment = (
                    modules.pricing.get_price(product=variant)
                    - modules.pricing.get_price(product=variant.product))
                
                print modules.pricing.get_price(product=variant)

            values = self.variation_value_seperator.join(
                [unicode(value)
                 for value in variation.values.all().order_by('attribute')]
            )

            choice = call_or_format(
                self.variation_choice_format,
                variation=variation,
                variant=variant,
                values=values,
                price_adjustment=price_adjustment)

        if chain:
            out = chain.execute(variation=variation, choice=choice, **kwargs)
            if out.has_key('choice'):
                choice = out['choice']
        return choice

    @chainable()
    def generate_variation_description(self, chain, prefix, values,
                                       description=None, **kwargs):
        if description is None:
            if values:
                values = self.variation_value_seperator.join(
                    [unicode(value) for value in values]
                )
            
                description = call_or_format(
                    self.variation_description_format,
                    prefix=prefix, values=values)
            else:
                description = prefix

        if chain:
            out = chain.execute(
                prefix=prefix, values=values,
                description=description, **kwargs)
            if out.has_key('description'):
                description = out['description']

        return description
