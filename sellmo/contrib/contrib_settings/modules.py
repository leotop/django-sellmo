# Copyright (c) 2012, Adaptiv Design
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
#    * Neither the name of the <ORGANIZATION> nor the names of its contributors may
# be used to endorse or promote products derived from this software without specific
# prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from django.core.cache import cache
from django.contrib.sites.models import Site
from django.db.models.signals import pre_save, pre_delete

#

from sellmo import modules, Module
from sellmo.core.local import get_context
from sellmo.magic import ModelMixin
from sellmo.api.decorators import view, chainable
from sellmo.contrib.contrib_settings.models import SiteSettings
from sellmo.contrib.contrib_settings.signals import setting_changed

#

class SettingsModule(Module):
    namespace = 'settings'
    SiteSettings = SiteSettings
    _settings = []
    
    def __init__(self, *args, **kwargs):
        # Add settings to SiteSettings
        grouped = {}
        for setting in self._settings:
            self.SiteSettings.add_to_class(setting[0], setting[1])
            group = setting[2]
            if group not in grouped:
                grouped[group] = []
            grouped[group].append(setting[0])
        
        self.fieldsets = tuple()
        for group in sorted(grouped.iterkeys()):
            fields = grouped[group]
            self.fieldsets += (
                (group, {
                    'fields' : fields   
                }),
            )
        
        # Hookup invalidation
        pre_save.connect(self.on_settings_pre_save, sender=self.SiteSettings)
        pre_delete.connect(self.on_settings_pre_delete, sender=self.SiteSettings)

    def on_settings_pre_save(self, sender, instance, created=False, **kwargs):
        self.on_cache_invalidated(instance)
        old = None
        if not created:
            old = self.SiteSettings.objects.get(pk=instance.pk)
        self.on_settings_changed(old, instance)
        
    def on_settings_pre_delete(self, sender, instance, **kwargs):
        self.on_cache_invalidated(instance)
        self.on_settings_changed(instance, None)
        
    def on_settings_changed(self, old, new):
        site = old.site if old is not None else new.site
        for key, field, group in self._settings:
            old_val = getattr(old, key, None) if old is not None else None
            new_val = getattr(new, key, None) if new is not None else None
            if old_val != new_val:
                setting_changed.send(sender=self, setting=key, old=old_val, new=new_val, site=site)

    def on_cache_invalidated(self, instance):
        cache.delete('site_settings_{0}'.format(instance.site.pk))
        
    def get_settings(self):
        context = get_context()
        settings = context.get('site_settings', None)
        if settings is None:
            site = Site.objects.get_current()
            if not site:
                raise Exception("Could not retrieve settings, no current site.")
            key = 'site_settings_{0}'.format(site.pk)
            settings = cache.get(key)
            if settings is None:
                try:
                    settings = self.SiteSettings.objects.get(site=site)
                except self.SiteSettings.DoesNotExist:
                    raise Exception("Could not retrieve settings, no settings found for site '{0}'".format(site))
                cache.set(key, settings)
            context['site_settings'] = settings
        return settings
    
    @classmethod
    def add_setting(self, key, field, group=None):
        self._settings.append((key, field, group))
        
        
