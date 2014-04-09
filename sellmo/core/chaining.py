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


import inspect
import functools
import logging

from sellmo.magic import singleton
from sellmo.signals.core import module_created, module_init

from django.http import HttpResponse


logger = logging.getLogger('sellmo')


def validate_func(func):
    if not callable(func):
        logger.warning(
            "Link '{0}.{1}' must be callable"
            .format(func.__module__, func.__name__))

    try:
        argspec = inspect.getargspec(func)
    except TypeError:
        try:
            argspec = inspect.getargspec(func.__call__)
        except (TypeError, AttributeError):
            argspec = None
    if argspec:
        if argspec[2] is None:
            logger.warning(
                "Link '{0}.{1}' must accept **kwargs"
                .format(func.__module__, func.__name__))


@singleton
class Chainer(object):

    def __init__(self):
        self._links = {}
        self._chains = {}
        self._modules = []
        module_init.connect(self.on_module_init)

    def hookup(self):
        # Fix bound links
        for module in self._modules:
            for name in dir(module):
                attr = getattr(module, name)
                if hasattr(attr, '_linked'):
                    path = attr._link_path
                    links = self._links[path]
                    link = filter(
                        lambda el: el['func'] == attr.__func__, links)[0]
                    link['func'] = attr

        # Hookup links
        for path, links in self._links.iteritems():
            # Find chain for this path
            if path not in self._chains:
                for link in links:
                    func = link['func']
                    logger.warning(
                        "Could not link '{0}.{1}' to '{2}'"
                        .format(func.__module__, func.__name__, path))
                continue

            # Hookup links to chain
            chain = self._chains[path]
            for link in links:
                validate_func(link['func'])
                chain.hookup(link['func'], capture=link['capture'])

        # Cleanup
        self._links = None
        self._chains = None
        self._modules = None

    def link(self, func, name=None, namespace=None, capture=False):
        if namespace is None:
            # Resolve namespace from func
            module = inspect.getmodule(func)
            if not module or not hasattr(module, 'namespace'):
                raise Exception(
                    "Link '{0}.{1}' has no target namespace."
                    .format(func.__module__, func.__name__))

            namespace = module.namespace

        if name is None:
            # Resolve name from func
            name = func.__name__

        # Map link
        path = '{0}.{1}'.format(namespace, name)
        if not path in self._links:
            self._links[path] = []
        self._links[path].append({
            'func': func,
            'capture': capture
        })

        # Flag this function so we can find it again and see if't a module's
        # instancemethod
        if inspect.isfunction(func):
            func._linked = True
            func._link_path = path

        return func

    def chain(self, chain):
        def wrapper(*args, **kwargs):
            return chain.handle(*args, **kwargs)
        wrapper = functools.update_wrapper(wrapper, chain._func)
        # Assign chain to wrapper, this allows us to map later on
        wrapper._chain = chain
        return wrapper

    def on_module_init(self, sender, module, **kwargs):
        self._modules.append(module)
        for name, attr in inspect.getmembers(type(module)):
            # Handle chain
            if hasattr(attr, '_chain'):
                chain = attr._chain
                # Map chain
                path = '{0}.{1}'.format(module.namespace, chain._func.__name__)
                self._chains[path] = chain


chainer = Chainer()


class Chain(object):

    def __init__(self, func):
        self._queue = []
        self._capture_queue = []
        self._func = func

    def hookup(self, link, capture=False):
        if capture:
            # Last link is captured first
            self._capture_queue.insert(0, link)
        else:
            # Last link is executed last
            self._queue.append(link)

    def handle(self, module, **kwargs):
        func = self._func

        # Capture
        out = self._loop(reversed(self._capture_queue), **kwargs)
        if not out[1] is None:
            if inspect.isfunction(out[1]):
                func = out[1]
            else:
                return out[1]

        kwargs = out[0]
        return func(module, self, **kwargs)

    def _loop(self, queue, **kwargs):
        for func in queue:
            # We allow for yieldable output
            if inspect.isgeneratorfunction(func):
                responses = list(func(**kwargs))
            else:
                responses = [func(**kwargs)]
            # Iterate through output
            for response in responses:
                if self.should_return(response):
                    # Return immediately
                    return (kwargs, response)
                elif isinstance(response, dict):
                    # Merge
                    kwargs.update(response)
                elif response is False:
                    # SKIP (1)
                    break
                elif response is None:
                    # Nothing to do, just keep on looping
                    continue
                else:
                    raise Exception(
                        "Func '{0}' gave an unexpected "
                        "response '{1}'."
                        .format(func, response))
            else:
                # No break in inner loop, continue
                continue
            # SKIP (2)
            break
        return (kwargs, None)

    def execute(self, **kwargs):
        out = self._loop(self._queue, **kwargs)
        if not out[1] is None:
            return out[1]
        return out[0]

    @property
    def can_execute(self):
        return len(self._queue) > 0

    @property
    def can_capture(self):
        return len(self._capture_queue) > 0

    def should_return(self, response):
        return inspect.isfunction(response)

    def __nonzero__(self):
        return self.can_execute

    def __repr__(self):
        return repr(self._func)


class ViewChain(Chain):

    def __init__(self, func, regex=None, **kwargs):
        super(ViewChain, self).__init__(func, **kwargs)
        self.regex = regex if not regex is None else []

    def handle(self, module, request, **kwargs):
        return super(ViewChain, self).handle(
            module=module, request=request, **kwargs)

    def capture(self, request, **kwargs):
        return super(ViewChain, self).capture(
            request=request, **kwargs)

    def execute(self, request, **kwargs):
        return super(ViewChain, self).execute(
            request=request, **kwargs)

    def should_return(self, response):
        return (isinstance(response, HttpResponse) or 
                super(ViewChain, self).should_return(response))
