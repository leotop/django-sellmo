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


from sellmo.api.http.query import QueryString

from django import template

from classytags.core import Tag, Options
from classytags.arguments import Argument


register = template.Library()


class QueryArgumentsValue(list):

    def __init__(self, query=None):
        list.__init__(self)
        self.query = query

    def resolve(self, context):
        if self.query is None:
            query = QueryString()
        else:
            query = self.query.resolve(context)
            if isinstance(query, QueryString):
                query = query.clone()
            else:
                query = QueryString()
        for value in self:
            key = value[0]
            operator = value[1]
            value = value[2].resolve(context)
            if operator == '=':
                query.set_param(key, value)
            elif operator == '+=':
                query.add_param(key, value)
            elif operator == '-=' and key in query:
                query.remove_param(key, value)
        return query


class QueryArguments(Argument):

    def __init__(self, name, default=None, required=True,
                 resolve=True, query=None):
        super(QueryArguments, self).__init__(name, default, required, resolve)
        self.query = query

    def parse_token(self, parser, token):
        if '+=' in token:
            operator = '+='
        elif '-=' in token:
            operator = '-='
        elif '=' in token:
            operator = '='
        else:
            raise template.TemplateSyntaxError(
                "QueryArguments arguments require key(=, +=, -=)value pairs"
            )

        key, raw_value = token.split(operator, 1)
        value = super(QueryArguments, self).parse_token(parser, raw_value)
        return key, operator, value

    def parse(self, parser, token, tagname, kwargs):
        if self.name not in kwargs:
            kwargs[self.name] = QueryArgumentsValue(
                kwargs[self.query] if self.query else None)
        kwargs[self.name].append(self.parse_token(parser, token))
        return True


class QueryTag(Tag):
    name = 'query'
    options = Options(
        QueryArguments('query'),
        'as',
        Argument('varname', default='query', required=False, resolve=False),
        blocks=[
            ('endquery', 'nodelist')
        ],
    )

    def render_tag(self, context, query, varname, nodelist):
        context.push()
        context[varname] = query
        output = nodelist.render(context)
        context.pop()
        return output


class ModQueryTag(Tag):
    name = 'modquery'
    options = Options(
        Argument('old'),
        QueryArguments('new', query='old'),
        'as',
        Argument('varname', default='query', required=False, resolve=False),
        blocks=[
            ('endmodquery', 'nodelist')
        ],
    )

    def render_tag(self, context, old, new, varname, nodelist):
        context.push()
        context[varname] = new
        output = nodelist.render(context)
        context.pop()
        return output

register.tag(QueryTag)
register.tag(ModQueryTag)
