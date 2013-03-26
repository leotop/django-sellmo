from django.db import models
from django.utils.translation import ugettext_lazy as _

from sellmo import modules
from sellmo.contrib.contrib_variation.models import Attribute, AttributeManager

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