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

# Singleton test
from singleton import SingletonMeta

#
class TheCar(object):
	
	__metaclass__ = SingletonMeta
	
	wheels = 0
	
	def __init__(self, wheels=0):
		self.wheels = wheels
		
	def __new__(cls, *args, **kwargs):
		obj = super(TheCar, cls).__new__(cls, *args, **kwargs)
		obj.tires = args[0]
		return obj
		
x = TheCar(4)
y = TheCar()

# 1
assert x.wheels == 4
assert x == y and x.wheels == y.wheels
assert x.tires == x.wheels
assert x.tires == y.tires

# 2
x.wheels = 2
assert y.wheels == 2

class ThePimpedCar(TheCar):
	
	is_pimped = True
	
	def __init__(self, wheels=0):
		super(ThePimpedCar, self).__init__(wheels=wheels)
		
	def __new__(cls, *args, **kwargs):
		obj = super(ThePimpedCar, cls).__new__(cls, *args, **kwargs)
		obj.color = 'purple'
		return obj
		
x1 = ThePimpedCar(6)
y1 = ThePimpedCar()

#1
assert x1 != x and y1 != y

#2
assert x.wheels == 2
assert x1.wheels == 6
assert x1 == y1 and x1.wheels == y1.wheels

#3
assert x1.is_pimped
assert not hasattr(x, 'is_pimped')
assert x1.tires == x1.wheels
assert x1.tires == y1.tires
assert x1.tires == 6
assert x.tires == 4

assert x1.color == 'purple'

