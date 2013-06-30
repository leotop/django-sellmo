from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response

from sellmo.api.decorators import link

@link()
def details(request, product, context, **kwargs):
    context['product'] = product
    context['category'] = product.primary_category
    context = RequestContext(request, context)
    return render_to_response('product/details.html', context)