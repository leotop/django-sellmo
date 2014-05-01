from sellmo import modules
from sellmo.api.decorators import link


from django.shortcuts import render


namespace = modules.account.namespace


@link()
def login(request, processed, redirection, context, **kwargs):
    if processed:
        return redirection
    return render(request, 'account/login.html', context)


@link()
def information_step(request, context, **kwargs):
    return render(request, 'account/information_step.html', context)
