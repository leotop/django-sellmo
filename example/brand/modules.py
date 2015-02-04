from sellmo import modules, Module
from sellmo.api.decorators import view, chainable, link, context_processor

from django.http import Http404
from django.utils.translation import ugettext_lazy as _

from brand.models import Brand


class BrandModule(Module):

    namespace = 'brand'
    Brand = Brand
    
    @context_processor()
    def brands_context(self, chain, request, context, **kwargs):
        if 'brands' not in context:
            context['brands'] = modules.brand.Brand.objects.all()
        return chain.execute(request=request, context=context, **kwargs)