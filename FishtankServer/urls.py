from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
	url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^content/', include('content.urls') ),
    url(r'^backup/', include('dtracker.urls') ),
    url(r'^manager/', include('manager.urls')),
)


