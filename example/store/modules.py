from sellmo import modules
from sellmo.api.decorators import view
from sellmo.api.http.query import QueryString

from django.shortcuts import render


class StoreModule(modules.store):
    
    prefix = ''
    
    @view(r'^$')
    def index(self, chain, request, context=None, **kwargs):
        if context is None:
            context = {}
        
        query = QueryString(request)
        featured = modules.product.Product.objects.filter(featured=True)
        featured = modules.product.list(request=request, products=featured, query=query).polymorphic()

        context.update({
            'featured': featured[:8]
        })

        return render(request, 'store/index.html', context)