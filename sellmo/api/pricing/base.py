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

from django.db import models
from decimal import Decimal

class Price(object):

	@staticmethod
	def _sanity_check(a, b):
		assert isinstance(a, Price), """Not a price"""
		assert isinstance(b, Price), """Not a price"""
		assert a.currency == b.currency, """Currency mismatch"""

	def __init__(self, amount=0, currency=None, type=None):
		self.amount = amount
		if not isinstance(self.amount, Decimal):
			self.amount = Decimal(str(self.amount))
		
		self.currency = currency
		self.type = type
		self._mutations = [(amount, type)]
		
	def __add__(a, b):
		Price._sanity_check(a, b)
		a.amount += b.amount
		a._mutations.extend(b._mutations)
		return a
		
	def __sub__(a, b):
		Price._sanity_check(a, b)
		a.amount -= b.amount
		a._mutations.extend((-mutation[0], mutation[1]) for mutation in b._mutations)
		return a
		
	def __mul__(a, b):
		Price._sanity_check(a, b)
		d = a.amount
		a.amount *= b.amount
		d = a.amount - d
		a._mutations.append((d, b.type))
		return a
		
	def __div__(a, b):
		Price._sanity_check(a, b)
		d = a.amount
		a.amount /= b.amount
		d = a.amount - d
		a._mutations.append((d, b.type))
		return a
		
	def __getitem__(self, key):
		if key:
			price = Price(0, self.currency, key)
			for mutation in self._mutations:
				if mutation[1] == key:
					price.amount += mutation[0]
			return price
		raise KeyError(key)
	
	def __unicode__(self):
		return unicode(self.amount)
		
	def __str(self):
		return str(self.amount)