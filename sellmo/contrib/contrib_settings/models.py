# Copyright (c) 2014, Adaptiv Design
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


from sellmo import modules
from sellmo.api.decorators import load

from django.db import models
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _


@load(action='finalize_settings_SiteSettings')
def finalize_model():
    class SiteSettings(modules.settings.SiteSettings):

        class Meta(modules.settings.SiteSettings.Meta):
            app_label = 'settings'
            verbose_name = _("site settings")
            verbose_name_plural = _("site settings")

    modules.settings.SiteSettings = SiteSettings


class SiteSettingsManager(models.Manager):

    def get_by_natural_key(self, site):
        return self.get(site=Site.objects.get_by_natural_key(site))


class SiteSettings(models.Model):
    site = models.OneToOneField(
        Site,
        related_name='settings',
    )

    def natural_key(self):
        return (self.site.natural_key(),)
    natural_key.dependencies = ['sites.site']

    def __unicode__(self):
        return unicode(self.site)

    class Meta:
        abstract = True
