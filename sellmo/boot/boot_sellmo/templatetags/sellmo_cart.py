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

from django import template
from django.core.urlresolvers import reverse

#

from sellmo import modules

#

register = template.Library()

#

@register.assignment_tag(takes_context=True)
def cart(context):
    return modules.cart.get(request=context['request'])

@register.inclusion_tag('cart/add_to_cart_formset.html', takes_context=True)
def add_to_cart_formset(context, product, next=None, invalid=None, **kwargs):
    formset = modules.cart.get_add_to_cart_formset(product=product, **kwargs) 
    data = formset.get_redirect_data(context['request'])
    if data:
        formset = modules.cart.get_add_to_cart_formset(product=product, data=data, **kwargs) 
    
    params = []
    if not next is None:
        params.append('next=%s' % next)
    if not invalid is None:
        params.append('invalid=%s' % invalid)
        
    inner = {
        'formset' : formset,
        'product' : product,
        'params' : params,
    }
    
    inner.update(kwargs)
    return inner
    
@register.inclusion_tag('cart/edit_purchase_form.html', takes_context=True)
def edit_purchase_form(context, purchase, next=None, invalid=None, **kwargs):
    form = modules.cart.get_edit_purchase_form(purchase=purchase, **kwargs)
    data = form.get_redirect_data(context['request'])
    if data:
        form = modules.cart.get_edit_purchase_form(purchase=purchase, data=data, **kwargs)
    
    params = []
    if not next is None:
        params.append('next=%s' % next)
    if not invalid is None:
        params.append('invalid=%s' % invalid)
    
    inner = {
        'form' : form,
        'purchase' : purchase,
        'params' : params,
    }
    
    inner.update(kwargs)
    return inner