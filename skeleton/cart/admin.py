from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from sellmo import modules

class PurchaseInline(admin.TabularInline):
    model = modules.store.Purchase

class CartAdmin(admin.ModelAdmin):
    inlines = [PurchaseInline]
    
admin.site.register(modules.cart.Cart, CartAdmin)