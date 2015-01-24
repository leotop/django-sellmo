from django.conf.urls import patterns, include

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    {% if not bare %}
    (r'^grappelli/', include('grappelli.urls')),
    {% endif %}
    (r'^admin/', include(admin.site.urls)),
    (r'', include('sellmo.core.urls')),
)
