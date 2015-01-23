from sellmo import modules
from sellmo.api.decorators import link


from django.shortcuts import render


namespace = modules.checkout.namespace


@link()
def login_step(request, context, **kwargs):
    return render(request, 'checkout/login.html', context)


@link()
def information_step(request, context, order, **kwargs):
    shipping = context['shipping_address_form']
    billing = context['billing_address_form']

    same_as_shipping = False
    if not request.method == 'POST':
        same_as_shipping = all(value == billing.initial[key]  for 
                               key, value in shipping.initial.iteritems()
                               if not key == 'id')

    if not same_as_shipping and request.POST.get('same_as_shipping', 'no') == 'yes':
        same_as_shipping = True
    
    context.update({
        'same_as_shipping': same_as_shipping
    })
    return render(request, 'checkout/information.html', context)


@link()
def payment_method_step(request, context, **kwargs):
    return render(request, 'checkout/payment_method.html', context)


@link()
def summary_step(request, context, **kwargs):
    return render(request, 'checkout/summary.html', context)


@link()
def complete(request, order, context, **kwargs):
    return render(request, 'checkout/complete.html', context)


@link()
def cancel(request, order, context, **kwargs):
    return render(request, 'checkout/cancel.html', context)