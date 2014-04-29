from sellmo import modules
from sellmo.api.decorators import link

from django.shortcuts import render


namespace = modules.category.namespace


@link()
def index(request, context, **kwargs):
    return render(request, 'category/index.html', context) 