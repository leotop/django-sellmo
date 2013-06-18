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
from sellmo.api.decorators import link
from sellmo.api.pricing import Price
from sellmo.contrib.contrib_variation.variation import find_variation

#

from django import forms
from django.forms.formsets import formset_factory
from django.contrib.contenttypes.models import ContentType


from sellmo import modules

#

@link(namespace=modules.product.namespace)
def list(request, products, **kwargs):
    flag = request.GET.get('variants', 'no').lower()
    if flag == 'yes':
        pass
    elif flag == 'only':
        products = products.exclude(content_type__in=ContentType.objects.get_for_models(*modules.product.subtypes).values())
    else:
        products = products.filter(content_type__in=ContentType.objects.get_for_models(*modules.product.subtypes).values())
    
    return {
        'products' : products
    }

@link(namespace=modules.pricing.namespace, name='get_price', capture=True)
def capture_get_price(product=None, **kwargs):
    out = {}
    
    if getattr(product, '_is_variant', False):
        out['variant'] = product
        product = product.product
    
    out['product'] = product
    return out
    
@link(namespace=modules.store.namespace)
def make_purchase(purchase, variation=None, **kwargs):
    if variation:
        purchase = modules.variation.VariationPurchase(
            product = purchase.product,
            qty = purchase.qty,
            variation_key = variation.key,
            variation_name = variation.name
        )
        
    return {
        'purchase' : purchase
    }

@link(namespace=modules.cart.namespace)
def get_purchase_args(form, product, args, **kwargs):
    if form.__class__.__name__ == 'AddToCartVariationForm':
        # Dealing with a varation form
        variation = find_variation(product, form.cleaned_data['variation'])
        if not variation:
            raise Exception()
        args['product'] = variation.product
        args['variation'] = variation
        
    return args

@link(namespace=modules.cart.namespace)
def get_add_to_cart_formset(formset, cls, product, variations=None, initial=None, data=None, **kwargs):
    
    if not variations:
        variations = product.variations
    
    # Before proceeding to custom form creation, check if we're dealing with a variation product
    if not variations:
        return
    
    # Create the custom form
    dict = {}
    
    # Add variation field as either a choice or as a hidden integer
    if not modules.variation.batch_buy_enabled and variations:
        dict['variation'] = forms.ChoiceField(
            choices = [(el.id, modules.variation.get_variation_choice(variation=el)) for el in variations]
        )
    else:
        dict['variation'] = forms.CharField(widget = forms.HiddenInput)
    
            
    AddToCartForm = type('AddToCartVariationForm', (cls,), dict)
        
    # Create the formset based upon the custom form
    AddToCartFormSet = formset_factory(AddToCartForm, extra=0)
    
    # Fill in initial data
    if not data:
        if modules.variation.batch_buy_enabled:
            initial = [{
                'product' : product.pk,
                'variation' : variation.id,
                'qty' : 1
            } for variation in variations]
        else:
            initial = [{
                'product' : product.pk,
                'variation' : variations[:1][0].id,
                'qty' : 1
            }]
            
        formset = AddToCartFormSet(initial=initial)
    else:
        formset = AddToCartFormSet(data)
        
    return {
        'formset' : formset,
        'variations' : variations
    }