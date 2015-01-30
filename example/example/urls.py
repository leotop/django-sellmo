from django.conf import settings
from django.conf.urls import patterns, include
from django.contrib import admin
from django.conf.urls.static import static

admin.autodiscover()

urlpatterns = patterns('',
    
    (r'^grappelli/', include('grappelli.urls')),
    
    (r'^admin/', include(admin.site.urls)),
    (r'', include('sellmo.core.urls')),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)