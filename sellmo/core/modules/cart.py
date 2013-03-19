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
from django.forms.formsets import formset_factory
from django.db import models
from django.http import Http404
from django.shortcuts import redirect

#

import sellmo
from sellmo import modules
from sellmo.api.decorators import view, chainable

#

class CartModule(sellmo.Module):

	namespace = 'cart'
	prefix = 'cart'
	enabled = True
	
	Cart = models.Model
	CartItem = models.Model
	AddToCartForm = forms.Form
	
	def __init__(self, *args, **kwargs):	
		from sellmo.api.cart.models import Cart
		self.Cart = Cart
		
		from sellmo.api.cart.models import CartItem
		self.CartItem = CartItem
		
		from sellmo.api.cart.forms import AddToCartForm
		self.AddToCartForm = AddToCartForm
	
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
			
			AddToCartFormSet = formset_factory(cls, extra=0)
			if not data:
				formset = AddToCartFormSet(initial=initial)
			else:
				formset = AddToCartFormSet(data)
				
		if chain:
			out = chain.execute(formset=formset, cls=cls, product=product, initial=initial, data=data, **kwargs)
			if out.has_key('formset'):
				formset = out['formset']
		
		return formset
		
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
			
	@view(r'$')
	def cart(self, chain, request, cart=None, context=None, **kwargs):
		if context == None:
			context = {}
			
		cart = self.Cart.objects.from_request(request)
		context['cart'] = cart
		
		if chain:
			return chain.execute(request, cart=cart, context=context, **kwargs)
		else:
			# We don't render anything
			raise Http404
		
	@view(r'add/(?P<product_slug>[a-z0-9_-]+)$')
	def add_to_cart(self, chain, request, product_slug, product=None, formset=None, purchases=None, context=None, **kwargs):
		
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
					
					# 
					purchase_args = self.get_purchase_args(product=product, form=form)
				
					# Try create the purchase
					purchase = modules.store.make_purchase(**purchase_args)
					if purchase:
						purchases.append(purchase)
		
		# Get the cart
		cart = self.Cart.objects.from_request(request)
		
		if purchases:	
			# Add purchases to cart
			for purchase in purchases:
				cart.add(purchase)
		
			# Keep track of our cart 
			cart.track(request)
		
		#
		if chain:
			return chain.execute(request, purchases=purchases, formset=formset, context=context, **kwargs)
		else:
			return redirect('cart.cart')
			