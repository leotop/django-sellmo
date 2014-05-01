from sellmo import modules
from sellmo.api.decorators import link


from django.shortcuts import render


namespace = modules.account.namespace


@link()
def login(request, context, **kwargs):
    return render(request, 'account/login.html', context)
