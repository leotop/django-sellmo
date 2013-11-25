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

from django import template
from django.core.urlresolvers import reverse

#

from classytags.core import Tag, Options
from classytags.arguments import Argument, MultiKeywordArgument, Flag

#

from sellmo import modules

#

register = template.Library()

#

class Customer(Tag):
    options = Options(
        Flag('authenticated', default=False, true_values=['authenticated']),
        MultiKeywordArgument('kwargs', required=False),
        'as',
        Argument('varname', default='customer', required=False, resolve=False),
        blocks = [('endcustomer', 'nodelist')],
    )

    def render_tag(self, context, authenticated, kwargs, varname, nodelist):
        customer = None
        if authenticated:
            if not modules.customer.django_auth_enabled:
                raise Exception("Customer authentication not enabled.")
            request = context['request']
            if request.user.is_authenticated() and hasattr(request.user, 'customer'):
                customer = request.user.customer
        else:
            customer = modules.customer.get_customer(request=context['request'], **kwargs)
        
        context.push()
        context[varname] = customer
        output = nodelist.render(context)
        context.pop()
        return output

register.tag(Customer)