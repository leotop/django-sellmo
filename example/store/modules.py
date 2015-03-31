from sellmo import modules
from sellmo.api.configuration import define_import
from sellmo.api.decorators import view, context_processor
from sellmo.api.http.query import QueryString
from sellmo.api.messaging import FlashMessages
from sellmo.core.mailing import mailer

from django.shortcuts import render, redirect


from store.models import IndexPage, GenericPage



class StoreModule(modules.store):
    
    prefix = ''
    
    
    ContactForm = define_import(
        'CONTACT_FORM',
        default='store.forms.ContactForm')
        
    @context_processor()
    def contact_form_context(self, chain, request, context, **kwargs):
        if 'contact_form' not in context:
            context['contact_form'] = self.ContactForm()
        return chain.execute(request=request, context=context, **kwargs)
    
    
    @view(r'^$')
    def index(self, chain, request, context=None, **kwargs):
        if context is None:
            context = {}
        
        qs = QueryString(request)
        featured = modules.product.Product.objects.filter(featured=True)
        featured = modules.product.list(request=request, products=featured, query=qs).polymorphic()
        
        context.update({
            'featured': featured[:8],
            'qs': qs
        })
        
        
        try:
            page = IndexPage.objects.all().latest_published()
        except IndexPage.DoesNotExist:
            page = None
        context.update({
            'page': page
        })
        

        return render(request, 'store/index.html', context)
        
    
    @view(r'^page/(?P<path>[-\w/]+)/$')
    def generic_page(self, chain, request, path, context=None, **kwargs):
        if context is None:
            context = {}
        
        try:
            page = GenericPage.objects.filter(path=path).latest_published()
        except GenericPage.DoesNotExist:
            raise Http404
        
        template = 'store/generic_page.html'
        if page.template:
            template = page.template
        
        context.update({
            'page': page,
        })
        
        return render(request, template, context)
    
    @view(r'^contact/$')
    def contact(self, chain, request, context=None, next=None, 
              invalid=None, messages=None, **kwargs):
                
        if messages is None:
            messages = FlashMessages()
        
        next = request.POST.get(
            'next', request.GET.get('next', next))
        invalid = request.POST.get(
            'invalid', request.GET.get('invalid', invalid))
        
        if context is None:
            context = {}
        
        redirection = None
        form = self.ContactForm(request.POST or None)
        context['contact_form'] = form
        
        if request.method == 'POST':
            if form.is_valid():
                redirection = redirect(next) if next else None
                mailer.send_mail('contact', {
                    'message' : form.cleaned_data['message'],
                    'name' : form.cleaned_data['name'],
                    'email' : form.cleaned_data['email']
                 })
            else:
                messages.error(request, get_error_message(form))
                redirection = redirect(invalid) if invalid else None
        
        if chain:
            return chain.execute(
                request, form=form, context=context, next=next, 
                invalid=invalid, redirection=redirection, messages=messages,
                **kwargs)
        elif redirection:
            messages.transmit()
            return redirection
        else:
            messages.clear()
            return render(request, 'store/contact.html', context)
    