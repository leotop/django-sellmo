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


from django import forms
from django.forms.formsets import formset_factory
from django.db import models
from django.db.models.signals import pre_delete
from django.http import Http404
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.module_loading import import_by_path
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext

import sellmo
from sellmo import modules
from sellmo.api.decorators import view, chainable, link, context_processor
from sellmo.api.exceptions import ViewNotImplemented
from sellmo.api.configuration import define_setting, define_import
from sellmo.api.cart.models import Cart
from sellmo.api.cart.forms import AddToCartForm, EditPurchaseForm
from sellmo.api.store.exceptions import PurchaseInvalid
from sellmo.api.messaging import FlashMessages
from sellmo.utils.forms import get_error_message


class CartModule(sellmo.Module):

    namespace = 'cart'
    enabled = True

    Cart = Cart
    
    AddToCartForm = define_import(
        'ADD_TO_CART_FORM',
        default='sellmo.api.cart.forms.AddToCartForm')
    
    EditPurchaseForm = define_import(
        'EDIT_PURCHASE_FORM',
        default='sellmo.api.cart.forms.EditPurchaseForm')

    def __init__(self):
        pre_delete.connect(self.on_delete_cart, sender=self.Cart)

    def on_delete_cart(self, sender, instance, **kwargs):
        # Purchases won't cascade on cart deletion
        for purchase in instance.purchases.all():
            if purchase.is_stale(ignore_cart=True):
                purchase.delete()

    @context_processor()
    def cart_context(self, chain, request, context, **kwargs):
        if 'cart' not in context:
            context['cart'] = self.get_cart(request=request)
        return chain.execute(request=request, context=context, **kwargs)

    @chainable()
    def get_edit_purchase_form(self, chain, form=None, cls=None, purchase=None, 
                               initial=None, data=None, **kwargs):
        if purchase is None:
            raise Exception()

        if cls is None:
            cls = self.EditPurchaseForm

        if form is None:
            if not data and not initial:
                initial = {
                    'purchase': purchase.pk,
                    'qty': purchase.qty
                }

            if not data:
                form = cls(initial=initial)
            else:
                form = cls(data)
        
        if chain:
            out = chain.execute(
                form=form, cls=cls, purchase=purchase,
                initial=initial, data=data, **kwargs)
            if out.has_key('form'):
                form = out['form']

        return form

    @chainable()
    def get_add_to_cart_formset(self, chain, product, formset=None, cls=None,
                                initial=None, data=None, **kwargs):
        product = product.downcast()

        if cls is None:
            cls = self.AddToCartForm

        if formset is None:
            if not data and not initial:
                initial = [{
                    'product': product.pk,
                }]

            AddToCartFormSet = formset_factory(
                cls, extra=0)
            if not data:
                formset = AddToCartFormSet(initial=initial)
            else:
                formset = AddToCartFormSet(data)
        
        if chain:
            out = chain.execute(
                formset=formset, cls=cls, product=product, 
                initial=initial, data=data, **kwargs)
            if out.has_key('formset'):
                formset = out['formset']

        return formset

    @chainable()
    def get_edit_purchase_args(self, chain, purchase, form, **kwargs):

        args = {
            'purchase': purchase,
        }

        if isinstance(form, self.EditPurchaseForm):
            args['qty'] = form.cleaned_data['qty']

        if chain:
            args = chain.execute(
                purchase=purchase, form=form, args=args, **kwargs)

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
            'product': product,
        }

        if isinstance(form, self.AddToCartForm):
            args['qty'] = form.cleaned_data['qty']

        if chain:
            out = chain.execute(
                product=product, form=form, args=args, **kwargs)
            args = out.get('args', args)

        # Purchase args should always contain
        # 'product', 'qty'
        if not args.has_key('product'):
            raise Exception("Purchase arg 'product' was not given.")
        if not args.has_key('qty'):
            raise Exception("Purchase arg 'qty' was not given.")

        return args

    @chainable()
    def get_cart(self, chain, request=None, cart=None, messages=None, 
                 **kwargs):
        
        messages_given = True
        if messages is None:
            messages_given = False
            messages = FlashMessages()
                 
        if cart is None:
            cart = self.Cart.objects.try_get_tracked(request)
        
        # Perform a sanity check on cart (and fix if needed)
        removals = []
        for purchase in cart:
            
            # Make sure no products have been deleted
            if purchase.product is None:
                removals.append(purchase)
            
            # Make sure this purchase is still valid
            try:
                modules.store.validate_purchase(request=request,
                                                purchase=purchase)
            except PurchaseInvalid as error:
                messages.error(request, error)
                removals.append(purchase)
            
        for purchase in removals:
            # ! Pass along the cart param to prevent recursion !
            self.remove_purchase(request=request, purchase=purchase, cart=cart)
        
        if removals:
            messages.warning(request, _("Your cart has been changed, one or "
                                      "more items are no longer valid."))
        
        if chain:
            out = chain.execute(cart=cart, request=request, messages=messages,
                                removals=removals, **kwargs)
            if out.has_key('cart'):
                cart = out['cart']
        
        if not messages_given:
            messages.transmit()
        
        return cart

    @view(r'^$')
    def cart(self, chain, request, cart=None, context=None, **kwargs):
        if context is None:
            context = {}

        cart = self.get_cart(request=request)
        context['cart'] = cart

        if chain:
            return chain.execute(request=request, cart=cart, context=context,
                                 **kwargs)
        else:
            raise ViewNotImplemented
    
    @method_decorator(require_POST)
    @view(r'^edit/(?P<purchase_id>[0-9]+)/$')
    def edit_purchase(self, chain, request, purchase_id, purchase=None,
                      form=None, context=None, next='cart.cart', 
                      invalid='cart.cart', messages=None, **kwargs):

        if messages is None:
            messages = FlashMessages()

        # Next and invalid params are allowed to be present into query
        next = request.POST.get(
            'next', request.GET.get('next', next))
        invalid = request.POST.get(
            'invalid', request.GET.get('invalid', invalid))

        if purchase is None:
            try:
                purchase = modules.store.Purchase.objects.polymorphic().get(
                    pk=purchase_id)
            except modules.store.Purchase.DoesNotExist:
                raise Http404

        if form is None:
            form = self.get_edit_purchase_form(
                purchase=purchase, data=request.POST)

        # Get the cart
        cart = self.get_cart(request=request, messages=messages)
        
        redirection = redirect(next)
        
        if 'remove' in request.POST:
            self.remove_purchase(request=request, purchase=purchase, cart=cart)
        else:
            # We require a valid form
            if form.is_valid():
                purchase_args = self.get_edit_purchase_args(
                    purchase=purchase, form=form)
                try:
                    purchase = modules.store.make_purchase(
                        request=request, **purchase_args)
                    self.update_purchase(
                        request=request, purchase=purchase, cart=cart)
                    messages.success(request, _("Your cart has been "
                                                "updated."))
                except PurchaseInvalid as error:
                    messages.error(request, _("Your cart could not be "
                                              "updated."))
                    messages.error(request, error)
                    redirection = redirect(invalid)
            else:
                messages.error(request, _("Your cart could not be "
                                          "updated."))
                messages.error(request, get_error_message(form))
                redirection = redirect(invalid)
        
        if chain:
            return chain.execute(
                request, purchase=purchase, form=form, context=context, 
                redirection=redirection, messages=messages, **kwargs)
        
        messages.transmit()
        return redirection

    @method_decorator(require_POST)
    @view(r'^add/(?P<product_slug>[-a-zA-Z0-9_]+)/$')
    def add_to_cart(self, chain, request, product_slug, product=None,
                    formset=None, purchases=None, context=None,
                    next='cart.cart', invalid='cart.cart', 
                    messages=None, **kwargs):
                    
        if messages is None:
            messages = FlashMessages()

        # Next and invalid params are allowed to be present into query
        next = request.POST.get(
            'next', request.GET.get('next', next))
        invalid = request.POST.get(
            'invalid', request.GET.get('invalid', invalid))

        if product is None:
            try:
                product = modules.product.Product.objects.polymorphic().get(
                    slug=product_slug)
            except modules.product.Product.DoesNotExist:
                raise Http404

        if context is None:
            context = {}

        if formset is None:
            formset = self.get_add_to_cart_formset(
                product=product, data=request.POST)
        
        redirection = redirect(next)
        
        # Purchase will in most cases not yet be assigned, 
        # it could be assigned however during the capture fase.
        if purchases is None:

            purchases = []

            # We require a valid formset
            if formset.is_valid():
                # get data from form
                for form in formset:
                    purchase_args = self.get_purchase_args(
                        product=product, form=form)
                    try:
                        purchase = modules.store.make_purchase(
                            request=request, **purchase_args)
                    except PurchaseInvalid as error:
                        messages.error(request, _("{0} could not be added to "
                                                  "your cart.")
                                                  .format(product))
                        messages.error(request, error)
                        redirection = redirect(invalid)
                        # We will redirect to invalid, but keep on adding
                        # valid purchases (in case multiple purchases are made)
                        continue
                    
                    purchases.append(purchase)
                    
            else:
                messages.error(request, _("Your cart could not be updated."))
                messages.error(request, get_error_message(formset))
                redirection = redirect(invalid)

        # Get the cart
        cart = self.get_cart(request=request, messages=messages)

        if purchases:
            # Add purchases to cart
            for purchase in purchases:
                try:
                    self.add_purchase(
                        request=request, purchase=purchase, cart=cart)
                    messages.success(request, _("{0} has been added to your "
                                              "cart.")
                                              .format(purchase.product))
                except PurchaseInvalid as error:
                    messages.error(request, _("{0} could not be added to "
                                              "your cart.")
                                              .format(purchase.product))
                    messages.error(request, error)
                    redirection = redirect(invalid)

            # Keep track of our cart
            cart.track(request)

        if chain:
            return chain.execute(
                request, product=product, purchases=purchases,
                formset=formset, context=context, redirection=redirection,
                next=next, invalid=invalid, messages=messages, **kwargs)

        messages.transmit()
        return redirection

    @chainable()
    def add_purchase(self, chain, request, cart=None, purchase=None, **kwargs):
        if cart is None:
            cart = self.get_cart(request=request)

        # See if we can merge this purchase
        merged = modules.store.merge_purchase(
            request=request, purchase=purchase,
            existing_purchases=list(cart))
        
        if merged:
            purchase = merged

        # Add to cart
        cart.add(purchase)

        if chain:
            chain.execute(
                request=request, purchase=purchase, cart=cart, **kwargs)

    @chainable()
    def update_purchase(self, chain, request, cart=None, purchase=None,
                        **kwargs):
        if cart is None:
            cart = self.get_cart(request=request)

        # See if we can merge this purchase
        merged = modules.store.merge_purchase(
            request=request, purchase=purchase,
            existing_purchases=list(cart))
        
        if merged:
            purchase = merged

        # Update cart
        cart.update(purchase)

        if chain:
            chain.execute(
                request=request, purchase=purchase, cart=cart, **kwargs)

    @chainable()
    def remove_purchase(self, chain, request, cart=None, purchase=None,
                        **kwargs):
        if cart is None:
            cart = self.get_cart(request=request)

        # Remove from cart
        if purchase in cart:
            cart.remove(purchase)

        if chain:
            chain.execute(
                request=request, purchase=purchase, cart=cart, **kwargs)

        # Now delete
        purchase.delete()
