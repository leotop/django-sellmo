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


from django.http import Http404

from sellmo import modules
from sellmo.api.decorators import link
from sellmo.api.pricing import Price
from sellmo.contrib.attribute.query import product_q

from django import forms
from django.forms.formsets import formset_factory
from django.contrib.contenttypes.models import ContentType


@link(namespace=modules.attribute.namespace, name='filter', capture=True)
def capture_filter(request, products, key, value, attribute=None,
                   operator=None, **kwargs):
    if not attribute:
        try:
            attribute = modules.attribute.Attribute.objects.get(key=key)
        except modules.attribute.Attribute.DoesNotExist:
            return

    yield {
        'attribute': attribute
    }

    if attribute.variates:
        yield override_filter


def override_filter(module, chain, request, products, key, value, attribute,
                    operator=None, **kwargs):
    try:
        value = attribute.parse(value)
    except ValueError:
        return products
        
    if operator is None:
        q = product_q(attribute, value) | product_q(
            attribute, value, through='base_product')
    else:
        qargs = {
            operator: value
        }
        q = (product_q(attribute, **qargs) |
             product_q(attribute, through='base_product', **qargs))
    
    return products.filter(q)


@link(namespace=modules.product.namespace)
def list(request, products, **kwargs):
    flag = request.GET.get('variants', 'no').lower()
    if flag == 'yes':
        pass
    elif flag == 'only':
        products = products.variants(only=True)
    else:
        products = products.variants(exclude=True)

    return {
        'products': products
    }


@link(namespace=modules.pricing.namespace, name='get_price', capture=True)
def capture_get_price(product=None, **kwargs):
    if product:
        out = {}
        product = product.downcast()
        if getattr(product, '_is_variant', False):
            out['variant'] = product
            product = product.product

        out['product'] = product
        return out


@link(namespace=modules.pricing.namespace)
def get_price(price, product=None, variant=None, **kwargs):
    if variant and variant.price_adjustment != 0:
        price += Price(variant.price_adjustment)
    return {
        'price': price
    }


@link(namespace=modules.store.namespace)
def make_purchase(purchase, variation=None, **kwargs):
    if variation:
        purchase = purchase.clone(cls=modules.variation.VariationPurchase)
        purchase.variation_key = variation.pk
        purchase.description = variation.description

    return {
        'purchase': purchase
    }


@link(namespace=modules.cart.namespace)
def get_purchase_args(form, product, args, **kwargs):
    if form.__class__.__name__ == 'AddToCartVariationForm':
        # Dealing with a varation form
        try:
            variation = modules.variation.Variation.objects.get(
                pk=form.cleaned_data['variation'])
        except modules.variation.Variation.DoesNotExist:
            raise Exception("Invalid variation")
        args['product'] = variation.variant.downcast()
        args['variation'] = variation

    return args


@link(namespace=modules.cart.namespace)
def get_add_to_cart_formset(formset, cls, product, variations=None,
                            initial=None, data=None, **kwargs):
    
    if variations is None and hasattr(product, 'get_variations'):
        variations = modules.variations.get_variations(product=product)
    
    # Before proceeding to custom form creation, check if we're dealing with a
    # variation product
    if not variations:
        return
        
    # Get attributes which variate the current variations from eachother
    attributes = modules.variation.get_variating_attributes(variations=variations)
    
    # Create the custom form
    dict = {
        'variations_key': forms.CharField(widget=forms.HiddenInput)
    }

    # Add variation field as either a choice or as a hidden integer
    if not modules.variation.batch_buy_enabled:
        dict['variation'] = forms.ChoiceField(
            label=modules.variation.generate_variation_label(attributes=attributes),
            choices=[(el.id, modules.variation.generate_variation_choice(
                        variation=el, attributes=attributes))
                      for el in variations]
        )
    else:
        dict['variation'] = forms.CharField(widget=forms.HiddenInput)

    AddToCartForm = type('AddToCartVariationForm', (cls,), dict)

    # Create the formset based upon the custom form
    AddToCartFormSet = formset_factory(
        AddToCartForm, extra=0)
    variations_key = '|'.join([variation.pk for variation in variations])

    # Fill in initial data
    if not data:
        if modules.variation.batch_buy_enabled:
            initial = [{
                'product': product.pk,
                'variation': variation.pk,
                'qty': 1,
                'variations_key': variations_key,
            } for variation in variations]
        else:
            initial = [{
                'product': product.pk,
                'variation': variations[:1][0].pk,
                'qty': 1,
                'variations_key': variations_key,
            }]

        formset = AddToCartFormSet(initial=initial)
    else:
        formset = AddToCartFormSet(data)
    
    return {
        'formset': formset,
    }


@link(namespace=modules.cart.namespace, name='add_to_cart', capture=True)
def capture_add_to_cart(request, product_slug, product=None, formset=None, 
                        **kwargs):

    if formset is None:
        data = request.POST
        variations_key = data.get('form-0-variations_key', None)
        if variations_key:

            # Resolve product
            if product is None:
                try:
                    product = modules.product.Product.objects.polymorphic() \
                                                     .get(slug=product_slug)
                except modules.product.Product.DoesNotExist:
                    raise Http404

            # Resolve variations
            variations = modules.variation.Variation.objects.filter(
                pk__in=variations_key.split('|'))

            # Get formset
            formset = modules.cart.get_add_to_cart_formset(
                product=product, variations=variations, data=data)

            return {
                'product': product,
                'formset': formset,
            }
