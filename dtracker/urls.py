from django.conf.urls.defaults import *
from mserver.dtracker.models import Torrent, Torrentclient
from django.views.generic.list_detail import object_list

# Databrowse suppot #
from django.contrib import databrowse
#databrowse.site.register(Torrent)
#databrowse.site.register(Torrentclient)

from django.views.generic import list_detail

info_dict = {'queryset':Torrent.objects.all(),}

urlpatterns = patterns('mserver.dtracker.views',
	# Main menu
 	#(r'^$',                             'main'),

	# two announce URL's to get around current django bug (#7379)
	(r'^announce/$',                   'announce'),
	(r'^announce$',                    'announce'),

	#upload torrent.
	(r'^upload/$',                     'uploadtorrent'),
	(r'^uploadsuccess/$',              'uploadsuccess'),

	#downloads 
	(r'^download/(?P<torrent_id>\d+)', 'downloadtorrent'),
	
	#torrent check
	(r'^check/$',                      'checktorrent'),
	
	(r'torrents/$', list_detail.object_list, info_dict)
	
	#databrowse
	#(r'^databrowse/(.*)', databrowse.site.root),
	
)


