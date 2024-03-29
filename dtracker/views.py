# views.py - Views for torrent tracker (dtracker)
#
# 8/22   - JFM, added checktorrent view.
# 7/2008 - Created


from django.http import HttpResponse
from cgi import parse_qs
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic.list_detail import object_list

from dtracker.bencode import bencode
from dtracker.models import Torrent, Torrentclient
from dtracker.forms import TorrentUploadForm

def main(request):
	
	list = Torrent.objects.all()
	
	response = object_list(request, list)
	return response
	
def announce(request):
	def _fail(reason):
		""" Helper function: creates an HTTP response for when errors occur in a way
			bittorrent clients can read.
		"""

		print
		print "Failure " + reason
		print
		return HttpResponse(bencode({'failure reason': reason}))

	# put all the request information into the c dict.
	c = {}
	
	# Get the minimum required fields for the torrent.
	try:
		c['addr']    = request.GET.get('ip', None) or request.META['REMOTE_ADDR']
		c['port']    = int(request.GET['port'])
		c['peer_id'] = request.GET['peer_id']

		# JFM, hack arond unicode issues with info_hash in django
		hash = parse_qs(request.META['QUERY_STRING'])['info_hash'][0].encode('hex')

	except KeyError:
		return _fail("""One of the following is missing: IP, Port, Peer_ID or info_hash""")

	# These fields may or may not come across, we hope they all do.
	c['event']      = request.GET.get('event',  'None') 
	c['uploaded']   = request.GET.get('uploaded', 0)
	c['downloaded'] = request.GET.get('downloaded',0)
	c['corrupt']    = request.GET.get('corrupt',0)
	c['remaining']  = request.GET.get('left',0)
	c['compact']    = request.GET.get('compact',0)
	c['numwant']    = request.GET.get('numwant',0)
	c['key']        = request.GET.get('key','none')

	try:	
		TheTorrent = Torrent.objects.get(info_hash=hash)
	except ObjectDoesNotExist:
		return _fail("Torrent is not registered, please upload your torrent first at /upload")

	# see if we have this client in the DB first.
	try:
		#if a user already eists, we're good.
		# Client.ob`jects.get(peer_id=c['peer_id'])
		TorrentClient = TheTorrent.torrentclient_set.get(ip=c['addr'])
		print "Found client "
		TorrentClient.port = c['port']
		TorrentClient.peer_id = c['peer_id']
	except ObjectDoesNotExist:
		#if the user doesn't exist, create one
		print "Adding new client " 
		TorrentClient = TheTorrent.torrentclient_set.create(ip=c['addr'], port=c['port'], peer_id=c['peer_id'])

	TorrentClient.addevent(values=c)
	TorrentClient.save()

	# Send back all clients that aren't us and are running (!stopped)
	clients = [{'ip': i.ip, 'peer id': i.peer_id, 'port': i.port} for i in TheTorrent.torrentclient_set.filter(stopped=False).exclude(ip=c['addr'])]

	r = {'peers': clients, 'interval': 1800	}

	try:
	    return HttpResponse(bencode(r))
	except:
		return _fail('Error encoding response.')

def uploadtorrent(request):

	if request.method == 'POST':
		print request.POST, "and", request.FILES
		form = TorrentUploadForm(request.POST, request.FILES)
		if form.is_valid():
			t = form.save()
			return HttpResponseRedirect('/backup/uploadsuccess/?id=%d' % t.id)
	else:
		form = TorrentUploadForm()
		
	return render_to_response('upload.html', {'form': form})

def uploadsuccess(request):
	if request.GET.has_key('id'):
		return HttpResponse("Sucess, your file was uploaded correctly.  ID = %s" % request.GET['id'])

def downloadtorrent(request, torrent_hash):
	t = get_object_or_404(Torrent, info_hash=torrent_hash)
	
	response = HttpResponse(open(t.file_path.path, "rb").read())
	response['Content-Type']='application/force-download'
	response['Content-disposition'] = 'attachment; filename=%s.torrent' % t.name
	return response 

	# response = HttpResponse(mimetype='application/vnd.ms-excel')
	# 	response['Content-Disposition'] = 'attachment; filename=' + t.file_path.path
	# return response

def checktorrent(request):
	if request.GET.has_key('info_hash'):
		try:
			hash = request.GET['info_hash']
			t = Torrent.objects.get(info_hash=hash)
			return HttpResponse('Found %s' % hash)
		except ObjectDoesNotExist:
			return HttpResponse('Torrent %s not found ' % hash)
	else:
		return HttpResponse('ERROR: you must pass a HASH parameter')
		