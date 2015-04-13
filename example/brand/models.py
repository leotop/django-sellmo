import os.path

from django.db import models
from django.utils.translation import ugettext_lazy as _

from sellmo import modules
from sellmo.api.decorators import load


def upload_image_to(instance, filename):
    return os.path.join('brand', instance.slug, filename)

    
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

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        ordering = ['name']


@load(action='finalize_brand_Brand')
def finalize_model():
    class Brand(modules.brand.Brand):
        class Meta(modules.brand.Brand.Meta):
            app_label = 'brand'

    modules.brand.Brand = Brand