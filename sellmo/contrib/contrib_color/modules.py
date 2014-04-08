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
from sellmo.api.decorators import view, chainable, link
from sellmo.contrib.contrib_color.models import Color, MultiColor, ColorMapping

from django.http import Http404
from django.utils.translation import ugettext_lazy as _

#


class ColorModule(Module):

    namespace = 'color'
    Color = Color
    MultiColor = MultiColor
    ColorMapping = ColorMapping

    def __init__(self):
        pass

    @chainable()
    def get_colors(self, chain, product=None, attribute=None, colors=None, **kwargs):
        if colors is None:
            if product:
                mappings = self.ColorMapping.objects.for_product(product)
            else:
                mappings = self.ColorMapping.objects.none()
            if attribute:
                mappings = mappings.for_attribute(attribute)
            colors = self.Color.objects.filter(
                pk__in=mappings.values_list('color', flat=True))

        if chain:
            out = chain.execute(
                product=product, attribute=attribute, colors=colors, **kwargs)
            if out.has_key('colors'):
                colors = out['colors']

        return colors
