from sellmo.magic.mixin import ModelMixin

from django.db import models
from django.contrib.admin.util import quote
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _


class LogEntryMixin(ModelMixin):

    model = LogEntry

    def get_admin_url(self):
        if self.content_type and self.object_id:
            model = self.content_type.model_class()
            if hasattr(model, 'get_admin_url'):
                return model.get_admin_url(
                    content_type=self.content_type, object_id=self.object_id)
            return (
                "{0}/{1}/{2}/"
                .format(
                    self.content_type.app_label,
                    self.content_type.model,
                    quote(self.object_id)))
        return None
