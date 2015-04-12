import os.path

from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet
from django.db.models.signals import pre_save, post_save, pre_delete
from django.utils.translation import ugettext_lazy as _

from sellmo import modules
from sellmo.api.decorators import load
from sellmo.contrib.attribute.query import value_q
from sellmo.contrib.attribute.adapter import AttributeTypeAdapter
from sellmo.magic import ModelMixin


# Media
def upload_image_to(instance, filename):
    return os.path.join('brand', instance.slug, filename)


class BrandAdapter(AttributeTypeAdapter):
    def get_choices(self):
        return modules.brand.Brand.objects.all()
        
    def parse(self, string):
        try:
            return modules.brand.Brand.objects.get(name__iexact=string)
        except modules.brand.Brand.DoesNotExist:
            raise ValueError()
    
class Brand(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("name")
    )
    
    slug = models.SlugField(
        max_length=80,
        db_index=True,
        unique=True,
        verbose_name=_("slug"),
        help_text=_(
            "Slug will be used in the address of"
            " the brand page. It should be"
            " URL-friendly (letters, numbers,"
            " hyphens and underscores only) and"
            " descriptive for the SEO needs."
        )
    )
    
    logo = models.ImageField(
        upload_to=upload_image_to,
        max_length=255,
        blank=True,
        verbose_name=_("logo"),
        help_text=_(
            "Black & white image of brand logo."
        )
    )
    
    short_description = models.TextField(
        blank=True,
        verbose_name=_("short description")
    )

    def polymorphic_natural_key(self):
        return (self.name,)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        ordering = ['name']


@load(action='finalize_brand_Brand')
@load(after='finalize_attribute_ValueObject')
def finalize_model():
    class Brand(modules.brand.Brand, modules.attribute.ValueObject):

        class Meta(modules.brand.Brand.Meta,
                   modules.attribute.ValueObject.Meta):
            app_label = 'attribute'
            verbose_name = _("brand")
            verbose_name_plural = _("brands")

    modules.brand.Brand = Brand
    
    
@load(before='finalize_attribute_Attribute')
def register_attribute_types():
    modules.attribute.register_attribute_type(
        'brand',
        BrandAdapter(),
        verbose_name=_("brand"))


@load(after='finalize_brand_Brand')
def load_manager():

    class BrandManager(modules.brand.Brand.objects.__class__):

        def get_by_polymorphic_natural_key(self, name):
            return self.get(name=name)

    class Brand(ModelMixin):
        model = modules.brand.Brand
        objects = BrandManager()


