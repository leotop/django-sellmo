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
from django.db import models
from django.http import Http404
from django.shortcuts import redirect

#

import sellmo
from sellmo import apps
from sellmo.store.decorators import view, get

#

class CartApp(sellmo.App):

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
	
	@get()
	def get_add_to_cart_form(self, chain, data=None, product=None, form=None, **kwargs):
		if form == None:
			if not data and not product:
				raise Exception("""Cannot create unbound form 'AddToCartForm'""")
			form = self.AddToCartForm(data)
		if chain:
			out = chain.execute(data=data, product=product, form=form, **kwargs)
			assert out.has_key('form'), """Form not returned"""
			return out['form']
		return form
			
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
		
	@view(r'add$')
	def add_to_cart(self, chain, request, purchase=None, context=None, **kwargs):
		"""
		view /cart/add/ (POST only)
		"""
		if context == None:
			context = {}
	
		# Purchase will in most cases not yet be assigned, it could be assigned however
		# during the capture fase.
		if not purchase:
			# get purchase from request
			if request.method == 'POST':
				form = self.get_add_to_cart_form(data=request.POST)
				if form.is_valid():
					
					# Process the form
					product = apps.product.Product.objects.get(id=form.cleaned_data['product'])
					
					# Create the purchase
					purchase = apps.store.make_purchase(product=product)
					
				if not purchase:
					raise Exception("""Purchase was not created""")
		
		# Add purchase to cart
		cart = self.Cart.objects.from_request(request)
		cart.add(purchase)
		cart.track(request)
		
		#
		if chain:
			return chain.execute(request, purchase=purchase, context=context, **kwargs)
		else:
			return redirect('cart.cart')
			