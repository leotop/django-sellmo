from sellmo import modules
from sellmo.api.decorators import view

class StoreModule(modules.store):
    
    prefix = ''
    
    @view(r'^$')
    def index(self, chain, request, **kwargs):
        pass