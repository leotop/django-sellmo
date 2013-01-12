from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from sellmo import modules
from sellmo.contrib.contrib_variation.admin import VariationAdminMixin, VariantForm, VariantFormSet
from sellmo.contrib.contrib_variation.models import Variable, Attribute
from sellmo.contrib.polymorphism.admin import PolymorphicParentModelAdmin

from product.admin.variation import VariableAdmin, AttributeAdmin
from pricing.admin import ProductQtyPriceInline

# Base admin for every product subtype
class ProductAdminBase(VariationAdminMixin, admin.ModelAdmin):
	
	inlines = [ProductQtyPriceInline]
	fieldsets = (
		(_("Product information"), {
			'fields': ('name', 'sku',)
		}),
		(_("Product pricing"), {
			'fields': ('tax',)
		}),
		(_("Product customization"), {
			'fields': ('custom_options',)
		}),
		(_("Webshop arrangement"), {
			'fields': ('slug', 'category', 'active', 'featured')
		})
	)
	
	filter_horizontal = ['category', 'custom_options']
	prepopulated_fields = {
		'slug' : ('name',),
	}
	
	
# Base inline admin for every variant subtype
class VariantInlineBase(admin.StackedInline):
	fieldsets = (
		(_("Product information"), {
			'fields': ('name', 'sku',)
		}),
		(_("Variant options"), {
			'fields': ('options',)
		}),
	)
	
	filter_horizontal = ['options']
	form = VariantForm
	formset = VariantFormSet

# Inline for simple product variant
class SimpleVariantInline(VariantInlineBase):
	model = modules.variation.SimpleProductVariant
	fk_name = 'product'
	
# Admin for simple product
class SimpleProductAdmin(ProductAdminBase):
	inlines = ProductAdminBase.inlines + [SimpleVariantInline]
	
# Admin for product
class ProductAdmin(PolymorphicParentModelAdmin):
	base_model = modules.product.Product
	child_models = [
		(modules.product.SimpleProduct, SimpleProductAdmin),
	]
	
	polymorphic_list = True
	list_display = ['name', 'active', 'featured', 'slug', 'sku', 'categories']
	list_display_links = ['name', 'slug']
	
	list_filter = ['active', 'featured']
	search_fields = ['name', 'slug', 'sku']
	
	def queryset(self, queryset):
		return modules.product.Product.objects.filter(content_type__in=ContentType.objects.get_for_models(*modules.product.subtypes).values())
	
	def categories(self, instance):
		return "<br/>".join([unicode(category) for category in instance.category.all()])
	
	categories.allow_tags = True
	categories.short_description = _("categories")
	
	def get_child_type_choices(self):
		choices = []
		for model, _ in [(modules.product.SimpleProduct, None),]:
			ct = ContentType.objects.get_for_model(model)
			choices.append((ct.id, model._meta.verbose_name))
		return choices
		
# Register admins
admin.site.register(modules.product.Product, ProductAdmin)
admin.site.register(Variable, VariableAdmin)
admin.site.register(Attribute, AttributeAdmin)

