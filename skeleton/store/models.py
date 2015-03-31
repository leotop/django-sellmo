{% if 'pages' in apps %}
from django.db import models
from django.utils.translation import ugettext_lazy as _

from pages.models import Page, PageManager


class IndexPage(Page):
    
    objects = PageManager()
    
    def __unicode__(self):
        return unicode(_("Index Page"))
    
    class Meta:
        app_label = 'pages'
        verbose_name = _("index page")
        verbose_name_plural = _("index pages")
        
        
class GenericPage(Page):
    
    objects = PageManager()
    
    path = models.CharField(
        max_length = 255,
    )

    title = models.CharField(
        blank = True,
        max_length = 140,
    )

    contents = models.TextField(
        blank = True,
    )

    def __unicode__(self):
        return self.path

    class Meta:
        app_label = 'pages'
        verbose_name = _("generic page")
        verbose_name_plural = _("generic pages")
        
    
{% endif %}