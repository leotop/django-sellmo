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


from django.core.cache import cache
from django.contrib.sites.models import Site
from django.contrib import admin
from django.db import models
from django.db.models.signals import pre_save, pre_delete

from sellmo import modules, Module
from sellmo.core.local import get_context
from sellmo.magic import ModelMixin
from sellmo.api.decorators import view, chainable, context_processor
from sellmo.contrib.settings.models import SiteSettings
from sellmo.contrib.settings.signals import setting_changed


class SettingsModule(Module):
    namespace = 'settings'
    SiteSettings = SiteSettings
    _settings = []
    _inline_settings = [] 

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
                    'fields': fields
                }),
            )

        # Hookup invalidation
        pre_save.connect(self.on_settings_pre_save, sender=self.SiteSettings)
        pre_delete.connect(
            self.on_settings_pre_delete, sender=self.SiteSettings)
            
    @context_processor()
    def settings_context(self, chain, request, context, **kwargs):
        if 'settings' not in context:
            try:
                context['settings'] = self.get_settings()
            except self.SiteSettings.DoesNotExist:
                pass
        return chain.execute(request=request, context=context, **kwargs)

    def on_settings_pre_save(self, sender, instance, **kwargs):
        self._on_cache_invalidated(instance)
        try:
            old = self.SiteSettings.objects.get(pk=instance.pk)
        except self.SiteSettings.DoesNotExist:
            old = None
            
        # The current request will still access the old settings, unless
        # we overwrite it manually at this point.
        context = get_context()
        settings = context['site_settings'] = instance
        self._settings_changed(old, instance)

    def on_settings_pre_delete(self, sender, instance, **kwargs):
        self._on_cache_invalidated(instance)
        
        # The current request will still access the old settings, unless
        # we overwrite it manually at this point.
        context = get_context()
        settings = context['site_settings'] = None
        self._settings_changed(instance, None)

    def _settings_changed(self, old, new):
        site = old.site if old is not None else new.site
        for key, field, group in self._settings:
            old_val = getattr(old, key, None) if old is not None else None
            new_val = getattr(new, key, None) if new is not None else None
            if old_val != new_val:
                setting_changed.send(
                    sender=self, setting=key, old=old_val,
                    new=new_val, site=site)

    def _on_cache_invalidated(self, instance):
        cache.delete('site_settings_{0}'.format(instance.site.pk))

    def get_settings(self):
        context = get_context()
        settings = context.get('site_settings', False)
        
        if settings is False:
            site = Site.objects.get_current()
            if site:
                # Try get settings from cache
                key = 'site_settings_{0}'.format(site.pk)
                settings = cache.get(key, settings)
        
        if not settings:
            if settings is False:
                try:
                    settings = self.SiteSettings.objects.get(site=site)
                except self.SiteSettings.DoesNotExist:
                    pass
                    
            if not settings:
                settings = self.SiteSettings()
            else:
                cache.set(key, settings)
                context['site_settings'] = settings
        
        return settings

    @classmethod
    def add_setting(self, key, field, group=None):
        self._settings.append((key, field, group))
    
    @classmethod
    def add_inline_setting(self, key, model, admin=admin.StackedInline):
        if not model._meta.abstract:
            raise Exception("Inline setting '{0}' needs to "
                            "be abstract".format(model))
        
        class Meta(model.Meta):
            app_label = 'settings'
        
        name = model.__name__
        attr_dict = {
            'Meta': Meta,
            '__module__': model.__module__,
            'settings': models.ForeignKey(
                'settings.SiteSettings',
                related_name=key)
        }
        
        model = type(name, (model,), attr_dict)
        self._inline_settings.append((model, admin))         
        