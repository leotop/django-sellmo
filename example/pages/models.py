from django.db import models
from django.db.models import Q
from django.conf import settings
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _


from sellmo.core.polymorphism import (PolymorphicQuerySet,
                                      PolymorphicManager,
                                      PolymorphicModel)


class PageQuerySet(PolymorphicQuerySet):

    def try_localized(self, language_code):
        return self.filter(Q(language=language_code) | Q(language=''))

    def latest_published(self):
        page = self.filter(publish=True)[:1]
        if not page:
            raise self.model.DoesNotExist
        return page[0]


class PageManager(PolymorphicManager):

    def __init__(self, cls=PageQuerySet):
        super(PageManager, self).__init__(cls)

    def latest_published(self, *args, **kwargs):
        return self.get_queryset().latest_published(*args, **kwargs)

    def try_localized(self, *args, **kwargs):
        return self.get_queryset().try_localized(*args, **kwargs)


class Page(PolymorphicModel):

    objects = PageManager()

    publish = models.BooleanField(
        default = True,
        verbose_name = _("publish"),
        help_text = (
            _("Only published pages are shown on the site.")
        )
    )

    publish_date = models.DateTimeField(
        verbose_name = _("publish date"),
        default = now
    )

    language = models.CharField(
        max_length = 2,
        blank = True,
        choices = [(k, v) for k, v in settings.LANGUAGES]
    )

    template = models.CharField(
        max_length = 255,
        blank = True
    )

    def describe(self):
        return self.pk

    def __unicode__(self):
        downcasted = self.downcast()
        return unicode(downcasted.describe())

    class Meta:
        ordering = ['publish_date']