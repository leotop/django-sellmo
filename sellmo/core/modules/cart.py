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
from django.contrib import messages
from django.forms.formsets import formset_factory
from django.db import models
from django.db.models.signals import pre_delete
from django.http import Http404
from django.shortcuts import redirect
from django.utils.module_loading import import_by_path

import sellmo
from sellmo.config import settings
from sellmo import modules
from sellmo.api.decorators import view, chainable, link
from sellmo.api.cart.models import Cart
from sellmo.api.cart.forms import AddToCartForm, EditPurchaseForm
from sellmo.api.forms import RedirectableFormSet


class CartModule(sellmo.Module):

    namespace = 'cart'
    prefix = 'cart'
    enabled = True

    Cart = Cart
    AddToCartForm = AddToCartForm
    EditPurchaseForm = EditPurchaseForm

    def __init__(self, *args, **kwargs):
        self.AddToCartForm = import_by_path(settings.ADD_TO_CART_FORM)
        self.EditPurchaseForm = import_by_path(settings.EDIT_PURCHASE_FORM)
        pre_delete.connect(self.on_delete_cart, sender=self.Cart)

    def on_delete_cart(self, sender, instance, **kwargs):
        for purchase in instance.purchases.all():
            if purchase.is_stale(ignore_cart=True):
                purchase.delete()

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

        form.set_redirect_key('edit_purchase_form_{0}'.format(purchase.pk))
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
                cls, extra=0, formset=RedirectableFormSet)
            if not data:
                formset = AddToCartFormSet(initial=initial)
            else:
                formset = AddToCartFormSet(data)

        formset.set_redirect_key('add_to_cart_formset_%s' % product.pk)
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
            raise Exception("Purchase arg 'product' was not given")
        if not args.has_key('qty'):
            raise Exception("Purchase arg 'qty' was not given")

        return args

    @chainable()
    def get_cart(self, chain, request=None, cart=None, **kwargs):
        if cart is None:
            cart = self.Cart.objects.from_request(request)
        if chain:
            out = chain.execute(cart=cart, request=request, **kwargs)
            if out.has_key('cart'):
                cart = out['cart']
        return cart

    @view(r'^$')
    def cart(self, chain, request, cart=None, context=None, **kwargs):
        if context is None:
            context = {}

        cart = self.get_cart(request=request)
        context['cart'] = cart

        if chain:
            return chain.execute(request, cart=cart, context=context, **kwargs)
        else:
            # We don't render anything
            raise Http404

    @view(r'^remove/(?P<purchase_id>[0-9]+)$')
    def remove_from_cart(self, chain, request, purchase_id, purchase=None,
                         context=None, **kwargs):

        next = request.GET.get('next', 'cart.cart')

        if purchase is None:
            try:
                purchase = modules.store.Purchase.objects.polymorphic().get(
                    pk=purchase_id)
            except modules.store.Purchase.DoesNotExist:
                raise Http404

        # Get the cart
        cart = self.get_cart(request=request)

        # Now remove from cart
        self.remove_purchase(request=request, cart=cart, purchase=purchase)

        redirection = redirect(next)
        if chain:
            return chain.execute(
                request, purchase=purchase, context=context,
                redirection=redirection, **kwargs)

        return redirection

    @view(r'^update/(?P<purchase_id>[0-9]+)$')
    def update_cart(self, chain, request, purchase_id, purchase=None,
                    form=None, context=None, **kwargs):

        next = request.GET.get('next', 'cart.cart')

        if purchase is None:
            try:
                purchase = modules.store.Purchase.objects.polymorphic().get(
                    pk=purchase_id)
            except modules.store.Purchase.DoesNotExist:
                raise Http404

        if form is None:
            if request.method == 'POST':
                form = self.get_edit_purchase_form(
                    purchase=purchase, data=request.POST)
            else:
                form = self.get_edit_purchase_form(
                    purchase=purchase, data=request.GET)

        # Get the cart
        cart = self.get_cart(request=request)

        # We require a valid formset
        if form.is_valid():
            purchase_args = self.get_edit_purchase_args(
                purchase=purchase, form=form)
            purchase = modules.store.make_purchase(**purchase_args)
            self.update_purchase(request=request, purchase=purchase, cart=cart)
        else:
            form.redirect(request)
            next = request.GET.get('invalid', 'cart.cart')

        redirection = redirect(next)
        if chain:
            return chain.execute(
                request, purchase=purchase, form=form,
                context=context, redirection=redirection, **kwargs)

        return redirection

    @view(r'^add/(?P<product_slug>[-a-zA-Z0-9_]+)$')
    def add_to_cart(self, chain, request, product_slug, product=None,
                    formset=None, purchases=None, context=None,
                    next='cart.cart', invalid='cart.cart', **kwargs):

        next = request.GET.get('next', next)
        invalid = request.GET.get('invalid', invalid)

        if product is None:
            try:
                product = modules.product.Product.objects.polymorphic().get(
                    slug=product_slug)
            except modules.product.Product.DoesNotExist:
                raise Http404

        if context is None:
            context = {}

        if formset is None:
            if request.method == 'POST':
                formset = self.get_add_to_cart_formset(
                    product=product, data=request.POST)
            else:
                formset = self.get_add_to_cart_formset(
                    product=product, data=request.GET)

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
                    purchase = modules.store.make_purchase(**purchase_args)
                    purchases.append(purchase)
            else:
                formset.redirect(request)
                redirection = redirect(invalid)

        # Get the cart
        cart = self.get_cart(request=request)

        if purchases:
            # Add purchases to cart
            for purchase in purchases:
                self.add_purchase(
                    request=request, purchase=purchase, cart=cart)

            # Keep track of our cart
            cart.track(request)

        if chain:
            return chain.execute(
                request,
                product=product,
                purchases=purchases,
                formset=formset,
                context=context,
                redirection=redirection,
                next=next,
                invalid=invalid,
                **kwargs
            )

        return redirection

    @chainable()
    def add_purchase(self, chain, request, cart=None, purchase=None, **kwargs):
        if cart is None:
            cart = self.get_cart(request=request)

        # See if we can merge this purchase
        merged = modules.store.merge_purchase(
            purchase=purchase, existing_purchases=list(cart))
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
            purchase=purchase, existing_purchases=list(cart))
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
