from django.db import models
from django.utils.translation import ugettext_lazy as _

from sellmo import modules
from sellmo.contrib.contrib_variation.models import Attribute, AttributeManager

# Customize the product base type
class Product(modules.product.Product):
	
	name = models.CharField(
		max_length = 120,
		verbose_name = _("name"),
		blank = False,
		
		# IMPORTANT !!! If we want to make variations work.
		null = True
	)

	sku = models.CharField(
		max_length = 60,
		verbose_name = _("sku"),
		blank = True,
		
		# IMPORTANT !!! If we want to make variations work.
		null = True
	)
	
	# Override default unicode convertion
	def __unicode__(self):
		if self.name:
			return self.name
		return super(Product, self).__unicode__()

	# IMPORTANT !!!
	class Meta:
		# App label needs to match this apps name
		# because we define this model as abstract.
		app_label = 'product'
		
		# Sellmo will make a concrete model at the
		# end of the boot cycle, this model needs to
		# be abstract in order to make polymorphism 
		# work and maintain a clean database schema.
		abstract = True

# Assign our custom type to Sellmo
modules.product.Product = Product

# Generic textual attribute
class SimpleAttribute(Attribute):

	# IMPORTANT !!! Custom manager is required in order to make attribute serialization work
	objects = AttributeManager()
	
	display = models.CharField(
		max_length = 120,
	)
	
	def __unicode__(self):
		return self.display
	
# An attribute that acts like a color
class ColorAttribute(Attribute):

	# IMPORTANT !!! Custom manager is required in order to make attribute serialization work
	objects = AttributeManager()

	name = models.CharField(
		max_length = 60,
	)
	
	color_code = models.CharField(
		max_length = 6,
	)
	
	def __unicode__(self):
		return self.name