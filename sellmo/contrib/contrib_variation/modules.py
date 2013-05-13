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

from sellmo import modules, Module
from sellmo.api.decorators import view, chainable
from sellmo.contrib.contrib_variation.models import Variation, VariationRecipe

from django.http import Http404
from django.utils.translation import ugettext_lazy as _

#

class VariationModule(Module):	

	namespace = 'variation'
	batch_buy_enabled = False
	Variation = Variation
	VariationRecipe = VariationRecipe
	
	def __init__(self):
		self.product_subtypes = []
		self.subtypes = []
		
	def register_product_subtype(self, subtype):
		self.product_subtypes.append(subtype)
		
	@view(r'add/(?P<product_slug>[a-z0-9_-]+)/(?P<variation_key>[a-z0-9_-]+)$')
	def add_to_cart(self, chain, request, product_slug, variation_key, **kwargs):
		try:
			product = modules.product.Product.objects.polymorphic().get(slug=product_slug)
		except modules.product.models.Product.DoesNotExist:
			raise Http404
			
		variation = product.find_variation(variation_key)
		if not variation:
			raise Http404
			
		if request.method == 'POST':
			formset = modules.cart.get_add_to_cart_formset(product=product, variation=variation, data=request.POST)
		else:
			formset = modules.cart.get_add_to_cart_formset(product=product, variation=variation, data=request.GET)
			
		return modules.cart.add_to_cart(request, product_slug=product_slug, product=product, formset=formset)
		
	@chainable()
	def get_sub_variation_label(self, chain, variation=None, **kwargs):
		# Get first child
		if not variation.children:
			raise Exception()
			
		sub = variation.children[0]
		if len(sub.options) == 1:
			return sub.options[0].variable.name
		return _("variation")
		
	@chainable()
	def get_variation_name(self, chain, variation=None, **kwargs):
		options = u' '.join([unicode(option.attribute) for option in variation.options])
		product = variation.product
		
		if hasattr(product, 'product'):
			product = product.product
		prefix = unicode(product)
		
		if not options:
			return prefix
		elif variation.parent:
			return options
			
		return '%s %s' % (prefix, options)
		
	@chainable()
	def get_variation_id(self, chain, variation=None, **kwargs):
		options = '_'.join([option.key for option in variation.options if option.custom])
		prefix = variation.product.slug
		
		if variation.parent:
			prefix = variation.parent.key
		if not options:
			return prefix
		
		return '%s_%s' % (prefix, options)