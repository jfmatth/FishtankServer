from django.conf.urls.defaults import *
from django.contrib import admin

from django.conf import settings


admin.autodiscover()

urlpatterns = patterns('',
	# root page will show nothing for now, except welcome.
    (r'^backup/', include('dtracker.urls')),
    
    (r'^manager/', include('manager.urls')),

    # Uncomment the next line for to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    
)

if settings.DEBUG:
    urlpatterns += patterns('',
		(r'^admin_media/(.*)', 
		 'django.views.static.serve',
		 {'document_root' : settings.ADMIN_MEDIA_ROOT,}
		),    
	)
    