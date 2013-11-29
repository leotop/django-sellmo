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
from django.utils.safestring import mark_safe

#

from sellmo import modules

#

from mptt.templatetags.mptt_tags import cache_tree_children

#

from classytags.core import Tag, Options
from classytags.arguments import Argument, MultiKeywordArgument, KeywordArgument, Flag

#

register = template.Library()

#

class CategoriesTag(Tag):
    name = 'categories'
    options = Options(
        Flag('nested', default=False, true_values=['nested']),
        MultiKeywordArgument('kwargs', required=False),
        'as',
        Argument('varname', default='categories', required=False, resolve=False),
        blocks = [
            ('node', 'pre_node'),
            ('endnode', 'node'),
            ('endcategories', 'post_node')
        ],
    )
    
    def _render_category_node(self, category, ancestors, current, context, nodelist):
        context.push()
        
        current_match = False
        if current:
            if current == category:
                current_match = 'exact'
            elif category.is_ancestor_of(current):
                current_match = True
        
        bits = []
        for child in category.get_children():
            _ancestors = ancestors + [category]
            _current = current if current_match else None
            bits.append(self._render_category_node(
                child,
                _ancestors,
                _current,
                context,
                nodelist
            ))
        
        context['node'] = category
        context['children'] = mark_safe(''.join(bits))
        context['current'] = current_match
        context['ancestors'] = ancestors
        context['absolute_url'] = category.get_absolute_url(slug=category.get_full_slug(ancestors=ancestors))
        context['path'] = ancestors + [category]
        output = nodelist.render(context)
        
        context.pop()
        return output

    def render_tag(self, context, nested, kwargs, varname, pre_node, node, post_node):
        current = None
        if 'current' in kwargs:
            current = kwargs.pop('current')
        
        categories = modules.category.list(nested=nested, **kwargs)
        if nested:
            categories = cache_tree_children(categories)
        
        context.push()
        context[varname] = categories
    
        nodes = []
        if node:
            nodes = [self._render_category_node(category, [], current, context, node) for category in categories]
            
        bits = [
            pre_node.render(context),
            mark_safe(''.join(nodes)),
            post_node.render(context)
        ]
        
        output = mark_safe(''.join(bits))
        context.pop()
        return output

register.tag(CategoriesTag)