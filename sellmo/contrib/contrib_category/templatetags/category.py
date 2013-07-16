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

register = template.Library()

#

@register.assignment_tag
def categories(parent=None):
    return modules.category.list(parent=parent)
    
@register.assignment_tag
def nested_categories(parent=None):
    return modules.category.list(parent=parent, nested=True)
        
@register.assignment_tag
def is_current(category, current_category=None):
    if not current_category:
        return False
    if current_category == category:
        return 'exact'
    if category.is_ancestor_of(current_category):
        return True
    return False
    
class RenderCategoriesNode(template.Node):
    def __init__(self, template_nodes, queryset_var):
        self.template_nodes = template_nodes
        self.queryset_var = queryset_var

    def _render_node(self, context, node, ancestors):
        bits = []
        context.push()
        for child in node.get_children():
            bits.append(self._render_node(context, child, ancestors + [node]))
        
        context['node'] = node
        context['children'] = mark_safe(''.join(bits))
        context['ancestors'] = ancestors
        context['absolute_url'] = node.get_absolute_url(slug=node.get_full_slug(ancestors=ancestors))
        context['path'] = ancestors + [node]
        
        rendered = self.template_nodes.render(context)
        context.pop()
        return rendered
    
    def render(self, context):
        queryset = self.queryset_var.resolve(context)
        roots = cache_tree_children(queryset)
        bits = [self._render_node(context, node, []) for node in roots]
        return ''.join(bits)


@register.tag
def render_categories(parser, token):
    bits = token.contents.split()
    if len(bits) != 2:
        raise template.TemplateSyntaxError(_("%s tag requires a queryset") % bits[0])

    queryset_var = template.Variable(bits[1])
    template_nodes = parser.parse(('endrender_categories',))
    parser.delete_first_token()
    return RenderCategoriesNode(template_nodes, queryset_var)