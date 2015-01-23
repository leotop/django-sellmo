from sellmo import modules
from sellmo.api.decorators import link

from django.shortcuts import render


namespace = modules.cart.namespace


@link()
def cart(request, context, **kwargs):
    return render(request, 'cart/cart.html', context) 