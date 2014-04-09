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


from django import template

from classytags.core import Tag, Options
from classytags.arguments import Argument, MultiKeywordArgument

from sellmo import modules
from sellmo.api.pricing import Price


register = template.Library()


class TiersTag(Tag):
    name = 'tiers'
    options = Options(
        MultiKeywordArgument('kwargs', required=False),
        'as',
        Argument('varname', default='tiers', required=False, resolve=False),
        blocks=[('endtiers', 'nodelist')],
    )

    def render_tag(self, context, kwargs, varname, nodelist):
        tiers = modules.qty_pricing.get_tiers(**kwargs)
        context.push()
        context[varname] = tiers
        output = nodelist.render(context)
        context.pop()
        return output

register.tag(TiersTag)


class TierTag(Tag):
    name = 'tier'
    options = Options(
        MultiKeywordArgument('kwargs', required=False),
        'as',
        Argument('varname', default='tier', required=False, resolve=False),
        blocks=[('endtier', 'nodelist')],
    )

    def render_tag(self, context, kwargs, varname, nodelist):
        tier = modules.qty_pricing.get_tier(**kwargs)
        context.push()
        context[varname] = tier
        output = nodelist.render(context)
        context.pop()
        return output

register.tag(TierTag)
