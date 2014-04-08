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

from django.http import Http404


#

from sellmo import modules, Module
from sellmo.api.decorators import view, chainable
from sellmo.contrib.contrib_category.models import Category

#


class CategoryModule(Module):
    namespace = 'category'
    Category = Category

    @chainable()
    def list(self, chain, parent=None, categories=None, nested=False, **kwargs):
        if categories is None:
            if parent:
                categories = parent.get_children().flat_ordered()
            else:
                if nested:
                    categories = self.Category.objects.all()
                else:
                    categories = self.Category.objects.root_nodes(
                    ).flat_ordered()

        categories = categories.active()

        if chain:
            out = chain.execute(
                parent=parent, categories=categories, nested=nested, **kwargs)
            categories = out.get('categories', categories)
        return categories

    @view(r'^$')
    def index(self, chain, request, context=None, **kwargs):
        if context is None:
            context = {}

        if chain:
            return chain.execute(request, context=context, **kwargs)
        else:
            # We don't render anything
            raise Http404

    @view(r'^(?P<full_slug>[-a-zA-Z0-9_/]+)/$')
    def category(self, chain, request, full_slug, category=None, context=None, **kwargs):
        if context is None:
            context = {}

        if category is None:
            parents = None
            categories = self.Category.objects.all()
            for slug in full_slug.split('/'):
                categories = self.Category.objects.filter(slug=slug)
                if parents is None:
                    categories = categories.filter(parent__isnull=True)
                else:
                    categories = categories.filter(parent__in=parents)

                # Get parent id's
                parents = categories.values_list('id', flat=True)
                if not parents:
                    break

            count = categories.count()
            if count == 0:
                raise Http404("Category '{0}' not found.".format(full_slug))
            elif count > 1:
                raise Http404(
                    "Category '{0}' could not be resolved.".format(full_slug))

            category = categories[0]

        if chain:
            return chain.execute(request, category=category, full_slug=full_slug, context=context, **kwargs)
        else:
            # We don't render anything
            raise Http404
