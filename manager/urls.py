from django.conf.urls.defaults import patterns

urlpatterns = patterns('manager.views',
    # Main menu
    (r'^$', 'main'),
    
    # client download link
    (r'^download/$', 'download'),
    
    # provides to register a new client to be managed.
    (r'^register/$', 'register'),
    
    (r'^dbmupload/$', 'dbmupload'),
        
    #get some files from the cloud for backup
    (r'^getcloud/$','getcloud'),
    
    # read / write settings to the manager.
    (r'^setting/(?P<guid>[-\w]+)/(?P<setting>\w+)/$', 'setting'),
     
)