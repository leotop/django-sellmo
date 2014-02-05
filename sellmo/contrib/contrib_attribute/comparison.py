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

#

class ValueComparator(object):
    def __init__(self, value):
        self.value = value
        
    def __eq__(self, other):
        a = self.value
        b = self.value
        return a.value == b.value and a.attribute.key == b.attribute.key
        
    def __hash__(self):
        return hash(u"attr_{0}_value_{1}".format(self.value.attribute.key, self.value.value))

class ValueSet(set):
    def __init__(self, values):
        values = [ValueComparator(value) for value in list(values)]
        super(ValueSet, self).__init__(values)
    
    def extract(self):
        for comparator in self:
            yield comparator.value
            
#

def _ordered(func):
    def wrap(a, b):
        c = func(ValueSet(a), ValueSet(b))
        for value in list(a) + list(b):
            if ValueComparator(value) in c:
                yield value
    return wrap

@_ordered
def difference(a, b):
    return a - b

@_ordered  
def intersection(a, b):
    return a & b
    
@_ordered
def union(a, b):
    return a + b
    
    