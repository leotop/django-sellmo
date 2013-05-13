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

def generate_slug(product, values=None, unique=False, full=False, short=False):

	if not values:
		values = list(product.attributes)
		
	sequences = []
	if not full:
		sequences.append('-'.join([unicode(value.get_value()) for value in values]))
	if not short:
		sequences.append('_'.join([u'%s-%s' % (value.attribute.key, unicode(value.get_value())) for value in values]))
	
	 
	for attributes in sequences:
		slug = u'%(prefix)s-%(attributes)s' % {
			'attributes' : attributes,
			'prefix' : product.slug
		}
		if not unique or VariantMixin.is_unique_slug(slug, ignore=product):
			return slug
	return slug

def is_unique_slug(slug, ignore=None):
	try:
		existing = modules.product.Product.objects.polymorphic().get(slug=slug)
	except modules.product.Product.DoesNotExist:
		return True
	
	return existing == ignore