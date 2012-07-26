from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'FishtankServer.views.home', name='home'),
    # url(r'^FishtankServer/', include('FishtankServer.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
	url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^content/', include('content.urls')),
    (r'^backup/', include('dtracker.urls')),
    (r'^manager/', include('manager.urls')),
)


