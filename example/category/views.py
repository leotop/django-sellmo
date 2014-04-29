from sellmo import modules
from sellmo.api.decorators import link
from sellmo.api.http.query import QueryString

from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


namespace = modules.category.namespace


@link()
def index(request, context, **kwargs):
    return render(request, 'category/index.html', context)
    

@link()
def category(request, category, context, **kwargs):
    query = QueryString(request)
    
    products = modules.product.Product.objects.in_category(category)
    products = modules.product.list(request=request, products=products, query=query).polymorphic()

    context.update({
        'products': _paginate(request, products),
        'category': category,
        #'index': products.index,
        'q': query
    })
    
    return render(request, 'category/category.html', context)


def _paginate(request, products):
    paginator = Paginator(products, 27)
    try:
        products = paginator.page(request.GET.get('page'))
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        products = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        products = paginator.page(paginator.num_pages)

    return products
