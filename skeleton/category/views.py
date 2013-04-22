from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response

from sellmo import modules
from sellmo.api.decorators import link

@link()
def category(request, category, context, **kwargs):
	context['category'] = category
	context['products'] = modules.product.Product.objects.in_category(category)
	context = RequestContext(request, context)
	return render_to_response('category/category.html', context)