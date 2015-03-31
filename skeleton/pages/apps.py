from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class DefaultConfig(AppConfig):
    name = 'pages'
    verbose_name = _("Site pages")