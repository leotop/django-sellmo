from sellmo import modules
from sellmo.api.decorators import link
from sellmo.api.http.query import QueryString

from django.shortcuts import render

from product.utils import paginate


namespace = modules.category.namespace


@link()
def index(request, context, **kwargs):
    return render(request, 'category/index.html', context)


@link()
def category(request, category, context, **kwargs):
    qs = QueryString(request)
    
    # Query all products in this category
    products = modules.product.Product.objects.in_category(category).polymorphic()
    
    # Pass queryset through product module and include http query
    # for further filtering and sorting
    products = modules.product.list(request=request, products=products, query=qs)
    
    # Get root category
    if not category.is_leaf_node():
        root = category
    elif category.is_child_node():
        root = category.parent
    else:
        root = category

    context.update({
        'products': paginate(request, products),
        'root': root,
        'category': category,
        'index': getattr(products, 'index', None),
        'qs': qs
    })

    return render(request, 'category/category.html', context)
