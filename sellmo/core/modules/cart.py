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

from django import forms
from django.contrib import messages
from django.forms.formsets import formset_factory
from django.db import models
from django.http import Http404
from django.shortcuts import redirect

#

import sellmo
from sellmo import modules
from sellmo.api.decorators import view, chainable
from sellmo.api.cart.models import Cart
from sellmo.api.cart.forms import AddToCartForm, EditCartForm
from sellmo.api.forms import RedirectableFormSet

#

class CartModule(sellmo.Module):

    namespace = 'cart'
    prefix = 'cart'
    enabled = True
    
    Cart = Cart
    
    AddToCartForm = AddToCartForm
    EditCartForm = EditCartForm
    
    def __init__(self, *args, **kwargs):        
        pass
        
    @chainable()
    def get_edit_cart_form(self, chain, form=None, cls=None, purchase=None, initial=None, data=None, **kwargs):
        if purchase is None:
            raise Exception()
            
        if cls is None:
            cls = self.EditCartForm
            
        if form is None:
            if not data and not initial:
                initial = {
                    'purchase' : purchase.pk,
                    'qty' : purchase.qty
                }
            
            if not data:
                form = cls(initial=initial)
            else:
                form = cls(data)
                
        form.set_redirect_key('edit_cart_form_%s' % purchase.pk)
        if chain:
            out = chain.execute(form=form, cls=cls, purchase=purchase, initial=initial, data=data, **kwargs)
            if out.has_key('form'):
                form = out['form']
        
        return form
        
    
    @chainable()
    def get_add_to_cart_formset(self, chain, formset=None, cls=None, product=None, initial=None, data=None, **kwargs):
        if product is None:
            raise Exception()
        else:
            product = product.downcast()
    
        if cls is None:
            cls = self.AddToCartForm
    
        if formset is None:
            if not data and not initial:
                initial = [{
                    'product' : product.pk,
                    'qty' : 1
                }]
            
            AddToCartFormSet = formset_factory(cls, extra=0, formset=RedirectableFormSet)
            if not data:
                formset = AddToCartFormSet(initial=initial)
            else:
                formset = AddToCartFormSet(data)
        formset.set_redirect_key('add_to_cart_formset_%s' % product.pk)
        if chain:
            out = chain.execute(formset=formset, cls=cls, product=product, initial=initial, data=data, **kwargs)
            if out.has_key('formset'):
                formset = out['formset']
        
        return formset
    
    @chainable()
    def get_edit_purchase_args(self, chain, purchase, form, **kwargs):
        
        args = {
            'purchase' : purchase,
        }
        
        if isinstance(form, self.EditCartForm):
            args['qty'] = form.cleaned_data['qty']
        
        if chain:
            args = chain.execute(purchase=purchase, form=form, args=args, **kwargs)
        
        # Purchase args should always contain
        # 'purchase', 'qty'
        if not args.has_key('purchase'):
            raise Exception("Purchase arg 'purchase' was not given")
        if not args.has_key('qty'):
            raise Exception("Purchase arg 'qty' was not given")
            
        return args
        
    @chainable()
    def get_purchase_args(self, chain, product, form, **kwargs):
        
        args = {
            'product' : product,
        }
        
        if isinstance(form, self.AddToCartForm):
            args['qty'] = form.cleaned_data['qty']
        
        if chain:
            args = chain.execute(product=product, form=form, args=args, **kwargs)
        
        # Purchase args should always contain
        # 'product', 'qty'
        if not args.has_key('product'):
            raise Exception("Purchase arg 'product' was not given")
        if not args.has_key('qty'):
            raise Exception("Purchase arg 'qty' was not given")
            
        return args
        
    @chainable()
    def get(self, chain, cart=None, request=None, **kwargs):
        if cart is None:
            cart = self.Cart.objects.from_request(request)
        
        if chain:
            out = chain.execute(cart=cart, request=request, **kwargs)
            if out.has_key('cart'):
                cart = out['cart']
        return cart
        
    @view(r'^$')
    def cart(self, chain, request, cart=None, context=None, **kwargs):
        if context == None:
            context = {}
            
        cart = self.get(request=request)
        context['cart'] = cart
        
        if chain:
            return chain.execute(request, cart=cart, context=context, **kwargs)
        else:
            # We don't render anything
            raise Http404
            
    @view(r'^edit/(?P<purchase_id>[0-9]+)$')
    def edit_cart(self, chain, request, purchase_id, purchase=None, form=None, context=None, **kwargs):
        
        target = request.GET.get('next', 'cart.cart')
        
        if purchase is None:
            try:
                purchase = modules.store.Purchase.objects.get(pk=purchase_id)
            except modules.store.Purchase.DoesNotExist:
                raise Http404
           
        if form is None:
            if request.method == 'POST':
                form = self.get_edit_cart_form(purchase=purchase, data=request.POST)
            else:
                form = self.get_edit_cart_form(purchase=purchase, data=request.GET)
                
        # Get the cart
        cart = self.get(request=request)
                
        # We require a valid formset
        if form.is_valid():
            purchase_args = self.get_edit_purchase_args(purchase=purchase, form=form)
            purchase = modules.store.edit_purchase(**purchase_args)
            cart.update(purchase)
            
            if chain:
                return chain.execute(request, purchase=purchase, form=form, context=context, **kwargs)
        else:
            form.redirect(request)
            target = request.GET.get('invalid', target)
        
        return redirect(target)
        
    @view(r'^add/(?P<product_slug>[a-z0-9_-]+)$')
    def add_to_cart(self, chain, request, product_slug, product=None, formset=None, purchases=None, context=None, **kwargs):
        
        target = request.GET.get('next', 'cart.cart')
        
        if product is None:
            try:
                product = modules.product.Product.objects.polymorphic().get(slug=product_slug)
            except modules.product.Product.DoesNotExist:
                raise Http404
        
        if context is None:
            context = {}
            
        if formset is None:
            if request.method == 'POST':
                formset = self.get_add_to_cart_formset(product=product, data=request.POST)
            else:
                formset = self.get_add_to_cart_formset(product=product, data=request.GET)
    
        # Purchase will in most cases not yet be assigned, it could be assigned however
        # during the capture fase.
        if purchases is None:
            
            purchases = []
            
            # We require a formset
            if not formset:
                raise Http404
            
            # We require a valid formset
            if formset.is_valid():
                
                # get data from form
                for form in formset:
                    purchase_args = self.get_purchase_args(product=product, form=form)
                    purchase = modules.store.make_purchase(**purchase_args)
                    purchases.append(purchase)
            else:
                print 'INVALID'
                formset.redirect(request)
                target = request.GET.get('invalid', target)
        
        # Get the cart
        cart = self.get(request=request)
        
        if purchases:   
            # Add purchases to cart
            for purchase in purchases:
                cart.add(purchase)
        
            # Keep track of our cart 
            cart.track(request)
            
            if chain:
                return chain.execute(request, purchases=purchases, formset=formset, context=context, **kwargs)
        
        return redirect(target)
            