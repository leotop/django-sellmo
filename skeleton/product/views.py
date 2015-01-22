from sellmo import modules
from sellmo.api.decorators import link

from django.shortcuts import render


namespace = modules.product.namespace


@link()
def product(request, product, context, **kwargs): 
    context.update({
        'product': product
    })
    return render(request, 'product/product.html', context) 