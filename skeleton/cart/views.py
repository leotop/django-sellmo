from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response

from sellmo.api.decorators import link

@link()
def cart(request, cart, context, **kwargs):
	context['cart'] = cart
	context = RequestContext(request, context)
	return render_to_response('cart/cart.html', context)