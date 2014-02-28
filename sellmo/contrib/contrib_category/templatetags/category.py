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
from django.conf import settings as django_settings
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.utils.safestring import mark_safe

#

from sellmo import modules
from sellmo.contrib.contrib_category.config import settings

#

from mptt.templatetags.mptt_tags import cache_tree_children

#

from classytags.core import Tag, Options
from classytags.arguments import Argument, MultiKeywordArgument, Flag

#

register = template.Library()

#

class CategoriesTag(Tag):
    name = 'categories'
    options = Options(
        Flag('nested', true_values=['nested'], false_values=['flat']),
        MultiKeywordArgument('kwargs', required=False),
        'cached',
        Argument('expire_time', default=False, required=False, resolve=False),
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
        
    def _render_categories(self, context, categories, current, pre_node, node, post_node):
        context.push()
        
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

    def render_tag(self, context, nested, kwargs, expire_time,  pre_node, node, post_node):
        current = None
        if 'current' in kwargs:
            current = kwargs.pop('current')
        
        cache_key = False
        output = None
        
        if not django_settings.DEBUG and expire_time is not False:
            cache_key = make_template_fragment_key('categories', [nested, current, str(pre_node + node + post_node)])
            output = cache.get(cache_key)
    
        if not output:
            # Query categories
            categories = modules.category.list(nested=nested, **kwargs)
            if nested:
                categories = cache_tree_children(categories)
            output = self._render_categories(context, categories, current, pre_node, node, post_node)            
            if cache_key:
                if expire_time is not None:
                    expire_time = int(expire_time)
                # Make sure we don't expire any longer than the categories_cache_keys entry
                if not settings.MAX_EXPIRE_TIME is None:
                    if expire_time is None or expire_time > settings.MAX_EXPIRE_TIME:
                        raise Exception("Expire time may not exceed {0}".format(settings.MAX_EXPIRE_TIME))
                
                cache.set(cache_key, output, expire_time)
                cache_keys = cache.get('categories_cache_keys', [])
                if cache_key not in cache_keys:
                    cache_keys.append(cache_key)
                cache.set('categories_cache_keys', cache_keys, settings.MAX_EXPIRE_TIME)
        
        return output

register.tag(CategoriesTag)