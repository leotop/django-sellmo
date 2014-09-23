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


from sellmo import modules, Module
from sellmo.api.configuration import define_import, define_setting
from sellmo.api.decorators import view, chainable
from sellmo.api.exceptions import ViewNotImplemented
from sellmo.contrib.payment.methods.mollie.models import MolliePayment
from sellmo.contrib.payment.methods.mollie.utils import (fix_amount,
                                                         generate_internal_id)

from django import forms
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.utils.module_loading import import_by_path
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

import requests

import Mollie


class MollieModule(Module):
    namespace = 'mollie'

    MolliePayment = MolliePayment

    IDealIssuerSelectForm = define_import(
        'IDEAL_ISSUER_SELECT_FORM',
        prefix='MOLLIE',
        default=('sellmo.contrib.payment.methods.mollie'
                 '.forms.IDealIssuerSelectForm'))
                 
    methods = define_setting(
        'METHODS',
        prefix='MOLLIE',
        transform=(lambda methods:
                   {k : import_by_path(v) 
                    for k, v in methods.iteritems()}),
        default={
            Mollie.API.Object.Method.IDEAL: 
                ('sellmo.contrib.payment.methods.mollie'
                 '.MollieIDealPaymentMethod'),
            Mollie.API.Object.Method.MISTERCASH: 
                ('sellmo.contrib.payment.methods.mollie'
                 '.MolliePaymentMethod')
        }
    )

    mollie_banklist_url = define_setting(
        'BANKLIST_URL',
        default='https://secure.mollie.nl/xml/ideal?a=banklist')

    mollie_fetch_url = define_setting(
        'FETCH_URL',
        default='https://www.mollie.nl//xml/ideal?a=fetch')

    mollie_check_url = define_setting(
        'CHECK_URL',
        default='https://secure.mollie.nl/xml/ideal?a=check')
        
    def _get_client(self):
        settings = modules.settings.get_settings()
        mollie = Mollie.API.Client()
        mollie.setApiKey(settings.mollie_api_key)
        return mollie
        
    @chainable()
    def get_methods(self, chain, methods=None, **kwargs):
        if methods is None:
            mollie = self._get_client()
            methods = {}
            for method in mollie.methods.all():
                identifier = method['id']
                if identifier in self.methods:
                    methods[identifier] = self.methods[identifier](
                        identifier,
                        name=method['description']
                    )
        if chain:
            out = chain.execute(methods=methods, **kwargs)
            methods = out.get('methods', methods)
        return methods

    @view()
    def ideal_issuer_select(self, chain, request, context=None, **kwargs):
        if context is None:
            context = {}
        if chain:
            return chain.execute(request=request, context=context, **kwargs)
        else:
            raise ViewNotImplemented

    @view()
    def pending(self, chain, request, context=None, **kwargs):
        if context is None:
            context = {}
        if chain:
            return chain.execute(request=request, context=context, **kwargs)
        else:
            raise ViewNotImplemented

    @view()
    def failure(self, chain, request, context=None, **kwargs):
        if context is None:
            context = {}
        if chain:
            return chain.execute(request=request, context=context, **kwargs)
        else:
            raise ViewNotImplemented

    @method_decorator(require_POST)
    @method_decorator(csrf_exempt)
    @view(r'^webhook/(?P<internal_id>[-a-zA-Z0-9_]+)/$')
    def webhook(self, chain, request, internal_id, **kwargs):
        mollie = self._get_client()
        
        try:
            order = self.MolliePayment.objects \
                        .get(internal_id=internal_id, 
                             external_id=request.POST['id']) \
                        .order
        except self.MolliePayment.DoesNotExist:
            raise Http404
        
        payment = mollie.payments.get(request.POST['id'])
        order.payment.update_transaction(payment)
        
        return HttpResponse('')

    @view(r'^back/(?P<internal_id>[-a-zA-Z0-9_]+)/$')
    def back(self, chain, request, internal_id, **kwargs):

        try:
            order = self.MolliePayment.objects \
                        .get(internal_id=internal_id) \
                        .order
        except self.MolliePayment.DoesNotExist:
            raise Http404

        # Hand over to checkout process
        return redirect(reverse('checkout.checkout'))

    @view()
    def redirect(self, chain, request, order, **kwargs):
        mollie = self._get_client()
        
        internal_id = generate_internal_id()
        
        method = order.payment.get_method()
        payment = mollie.payments.create(dict({
            'amount'      : fix_amount(order.total.amount),
            'description' : unicode(order),
            'webhookUrl': request.build_absolute_uri(
                reverse('mollie.webhook', args=(internal_id,))),
            'redirectUrl': request.build_absolute_uri(
                reverse('mollie.back', args=(internal_id,))),
        }, **method.get_mollie_kwargs(order=order)))

        order.payment.new_transaction(internal_id, payment)

        if chain:
            return chain.execute(request=request, **kwargs)
        else:
            return redirect(payment.getPaymentUrl())

    @chainable()
    def get_ideal_issuer_select_form(self, chain, prefix=None, data=None,
                                     form=None, issuer=None, issuers=None,
                                     **kwargs):
        if issuers is None:
            issuers = self.get_ideal_issuers()
        if form is None:
            class IDealIssuerSelectForm(self.IDealIssuerSelectForm):
                issuer = forms.ChoiceField(
                    widget=forms.RadioSelect(),
                    choices=[(k, v) for k, v in issuers.iteritems()]
                )
            initial = {}
            if issuer:
                initial['issuer'] = issuer
            form = IDealIssuerSelectForm(data, prefix=prefix, initial=initial)
        if chain:
            out = chain.execute(prefix=prefix, data=data, form=form, **kwargs)
            if out.has_key('form'):
                form = out['form']
        return form

    @chainable()
    def get_ideal_issuers(self, chain):
        mollie = self._get_client()
        issuers = mollie.issuers.all()
        return {issuer['id']: issuer['name'] for issuer in issuers}

    @chainable()
    def process_ideal_issuer_select(self, chain, request, payment, prefix=None, 
                                    data=None, issuer=None, **kwargs):
        issuers = self.get_ideal_issuers()
        processed = False
        initial = None

        if payment.issuer is not None:
            initial = payment.issuer

        form = self.get_ideal_issuer_select_form(prefix=prefix, data=data, 
                                                 issuers=issuers,
                                                 issuer=initial)

        if data and form.is_valid():
            # Resolve issuer
            issuer = form.cleaned_data['issuer']
            payment.issuer = issuer
            processed = True

        if chain:
            out = chain.execute(
                request=request, payment=payment, prefix=prefix,
                data=data, issuer=issuer, form=form, processed=processed,
                **kwargs
            )
            issuer, form, processed = (
                out.get('issuer', issuer),
                out.get('form', form),
                out.get('processed', processed)
            )
        return issuer, form, processed
