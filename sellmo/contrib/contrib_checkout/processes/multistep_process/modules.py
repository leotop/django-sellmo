# Copyright (c) 2014, Adaptiv Design
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


from django.http import Http404
from django.shortcuts import redirect

from sellmo import modules
from sellmo.api.decorators import chainable, view


class CheckoutModule(modules.checkout):

    @chainable()
    def get_checkout_step(self, chain, key, order, request, step=None, **kwargs):
        if chain:
            out = chain.execute(
                key=key, order=order, request=request, step=step)
            step = out.get('step', step)
        return step
    
    @view()
    def checkout_information(self, chain, request, context=None, **kwargs):
        if context is None:
            context = {}

        if chain:
            return chain.execute(request=request, context=context, **kwargs)
        else:
            # We don't render anything
            raise Http404

    @view()
    def checkout_payment_method(self, chain, request, context=None, **kwargs):
        if context is None:
            context = {}

        if chain:
            return chain.execute(request=request, context=context, **kwargs)
        else:
            # We don't render anything
            raise Http404

    @view()
    def checkout_summary(self, chain, request, context=None, **kwargs):
        if context is None:
            context = {}

        if chain:
            return chain.execute(request=request, context=context, **kwargs)
        else:
            # We don't render anything
            raise Http404
