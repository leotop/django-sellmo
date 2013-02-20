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
		
class _AttributeMeta(object):
	def __init__(self, attribute):
		self.attribute = attribute
		self.variants = []
		self.custom = False

def get_variations(product):
	variables = {}
	
	# Collect variables from variants
	for variant in product.variants.all():
		for option in variant.options.all():
			if not variables.has_key(option.variable):
				variables[option.variable] = _VariableMeta(option.variable)
			
			variable = variables[option.variable]
			if not variable.attributes.has_key(option.attribute):
				variable.attributes[option.attribute] = _AttributeMeta(option.attribute)
			variable.attributes[option.attribute].variants.append(variant)
	
	# Collect variables from custom variables
	if modules.variation.custom_options_enabled:
		for option in product.custom_options.all():
			if not variables.has_key(option.variable):
				variables[option.variable] = _VariableMeta(option.variable)
			
			variable = variables[option.variable]
			if not variable.attributes.has_key(option.attribute):
				variable.attributes[option.attribute] = _AttributeMeta(option.attribute)
			variable.attributes[option.attribute].custom = True
			
	def _construct(*options):
		variants = None
		for variable, attribute in options:
			if variants is None:
				variants = list(attribute.variants)
				
			for variant in list(variants):
				if (variant.variables.count(variable.variable) and not variant.attributes.count(attribute.attribute)) \
				or (not attribute.custom and not variant.variables.count(variable.variable)):
					variants.remove(variant)
		
		variant = product if not variants else variants[0] 
		return Variation(variant, [Option(option[0].variable, option[1].attribute) for option in options])
			
	def _variate(variables, *options):
		variations = []
		if not variables:
			# Construct variation at this point
			variations.append(_construct(*options))
		else:
			# Recurse iterate through all possible combinations
			variable = variables[0]
			for attribute in variable.attributes.values():
				variations.extend(
					_variate(variables[1:], *(list(options) + [(variable, attribute)]))
				)
		
		return variations
	return _variate(variables.values())
	
class Option(object):
	def __init__(self, variable, attribute):
		self.variable = variable
		self.attribute = attribute
		
	@property
	def key(self):
		return '%s-%s' % (self.variable.name, self.attribute.value)
	
class Variation(object):
	def __init__(self, product, options):
		self.product = product
		self.options = options
		
	@property
	def key(self):
		return '%s___%s' % (self.product.slug, '_'.join([option.key for option in self.options]))
		
	@property
	def json(self):
		pass
		
	def __unicode__(self):
		return self.key
	
