from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from sellmo import modules
from sellmo.api.decorators import link

@link()
def category(request, category, context, **kwargs):
    context['category'] = category
    
    # Get products
    q = modules.product.Product.objects.polymorphic().in_category(category)
    q = modules.product.list(request=request, products=q)
    paginator = Paginator(q, 25)
    try:
        products = paginator.page(request.GET.get('page'))
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        products = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        products = paginator.page(paginator.num_pages)
    
    context['products'] = products
    context = RequestContext(request, context)
    return render_to_response('category/category.html', context)