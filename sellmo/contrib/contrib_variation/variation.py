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

from sellmo import modules

#

class _VariableMeta(object):
	def __init__(self, variable):
		self.variable = variable
		self.attributes = {}
		self.custom = False
		
class _AttributeMeta(object):
	def __init__(self, attribute):
		self.attribute = attribute
		self.variants = []
		self.custom = False
		
def find_variation(product, key):

	def _find(variations, key):
		for variation in variations:
			if variation.key == key:
				return variation
		return None

	# First we try primary variations
	variations = get_variations(product)
	variation = _find(variations, key)
	if variation:
		return variation
	
	# No luck, lets try all variations
	variations = get_variations(product, all=True)
	variation = _find(variations, key)
	if variation:
		return variation
		
	return None
	

def get_variations(product, all=False):
	variables = {}
	
	# Collect variables from variants
	for variant in product.variants.all().prefetch_related('options__variable', 'options__attribute'):
		for option in variant.options.all():
			if not variables.has_key(option.variable):
				variables[option.variable] = _VariableMeta(option.variable)
			
			variable = variables[option.variable]
			if not variable.attributes.has_key(option.attribute):
				variable.attributes[option.attribute] = _AttributeMeta(option.attribute)
			variable.attributes[option.attribute].variants.append(variant)
	
	# Collect variables from custom variables
	if modules.variation.custom_options_enabled:
		for option in product.custom_options.all().prefetch_related('variable', 'attribute'):
			if not variables.has_key(option.variable):
				variables[option.variable] = _VariableMeta(option.variable)
			
			variable = variables[option.variable]
			if not variable.attributes.has_key(option.attribute):
				variable.attributes[option.attribute] = _AttributeMeta(option.attribute)
			variable.attributes[option.attribute].custom = True
			variable.custom = True
	
	def _construct(options, custom_variables):
		
		def _has_variable(variant, variable):
			return [option.variable for option in variant.options.all()].count(variable.variable) == 1
			
		def _has_attribute(variant, attribute):
			return [option.attribute for option in variant.options.all()].count(attribute.attribute) == 1
	
		variants = None
		for variable, attribute in options:
			if variants is None:
				variants = list(attribute.variants)
				
			for variant in list(variants):			
				if (_has_variable(variant, variable) and not _has_attribute(variant, attribute)) or (not attribute.custom and not _has_variable(variant, variable)):
					variants.remove(variant)
		
		variant = product if not variants else variants[0]
		children = []
		if custom_variables:
			children = _variate(custom_variables, [], [], all=True)
		
		return Variation(variant, [Option(option[0].variable, option[1].attribute, option[1].custom) for option in options], children)
			
	def _variate(variables, options, custom_variables, all=False):
		variations = []
		if not variables:
			# Construct variation at this point
			variations.append(_construct(options, custom_variables))
		else:
			# Recurse iterate through all possible combinations
			variable = variables[0]
			if not variable.custom or all:
				for attribute in variable.attributes.values():
					variations.extend(
						_variate(variables[1:], options + [(variable, attribute)], custom_variables, all=all)
					)
			else:
				variations.extend(
					_variate(variables[1:], options, custom_variables + [variable], all=all)
				)
		
		return variations
	
	return _variate(variables.values(), [], [], all=all)
	
class Option(object):
	def __init__(self, variable, attribute, custom):
		self.variable = variable
		self.attribute = attribute
		self.custom = custom
		
	@property
	def key(self):
		return '%s-%s' % (self.variable.name, self.attribute.value)
	
class Variation(object):
	parent = None
	def __init__(self, product, options, children):
		self.product = product
		self.options = options
		self.children = children if not children is None else []
		for variation in self.children:
			variation.parent = self
		
	@property
	def key(self):
		return modules.variation.get_variation_key(variation=self)
		
	@property
	def name(self):
		return modules.variation.get_variation_name(variation=self)
		
	def __unicode__(self):
		return self.name
	
