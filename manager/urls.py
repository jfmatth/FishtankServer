from django.conf.urls.defaults import patterns

urlpatterns = patterns('manager.views',
    # Main menu
     (r'^$', 'main'),

     # client download link
     (r'^download/$', 'download'),
     
     # provides to register a new client to be managed.
     (r'^register/$', 'register'),
     
     (r'^uploadtest/$', 'uploadtest'),

     (r'^dbmupload/$', 'dbmupload'),
     
     # read / write settings to the manager.
     (r'^setting/(?P<guid>[-\w]+)/(?P<setting>\w+)/$', 'setting'),
     
)