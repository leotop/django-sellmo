from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from sellmo import modules

class CartItemInline(admin.TabularInline):
	model = modules.cart.CartItem

class CartAdmin(admin.ModelAdmin):
	inlines = [CartItemInline]
	
admin.site.register(modules.cart.Cart, CartAdmin)