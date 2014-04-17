from sellmo import modules
from sellmo.api.decorators import view

from django.shortcuts import render

class StoreModule(modules.store):
    
    prefix = ''
    
    @view(r'^$')
    def index(self, chain, request, **kwargs):
        return render(request, 'store/index.html')