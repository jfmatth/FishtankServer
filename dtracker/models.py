from django.db import models
from django.contrib.auth import models as auth_models
import datetime
from dtracker.bencode import bdecode, bencode
from sha import *

class TorrentCountManager(models.Manager):
	# returns a list of torrents that have less than 3 clients, hard coded 3 for now, will figure more out later.
	def get_query_set(self):
		return super(TorrentCountManager, self).get_query_set().extra( where = ['(select count(*) from dtracker_torrentclient_torrents where dtracker_torrent.id = dtracker_torrentclient_torrents.torrent_id) < 3'])

class Torrent(models.Model):
	name	  = models.CharField(max_length=200, blank=True)
	file_path = models.FileField("File location", upload_to='torrents', blank=True)
	info_hash = models.CharField("Info Hash", max_length=40, blank=True)
	size	  = models.IntegerField(blank=True, null=True)
	announce  = models.CharField("HTTP announce",max_length=100, blank=True)
	piece_length = models.IntegerField(blank=True, null=True)
	
	# standard and Custom manager for counting how many clients hve this torrent.
	objects       = models.Manager()
	needclients   = TorrentCountManager()

	def __unicode__(self):
		return self.name
	
	# need to modify the save() routine to update the various fields, once the file is uploaded.
	def save(self):
		print "saving"

		if self.id == None:
			print "self id is none"
			# only calculate for new records.
			super(Torrent, self).save()
			
			self.fillin_torrent_fields()

		print "saving2"
		super(Torrent,self).save()

	# pretty kludgy but it works?
	def fillin_torrent_fields(self):	
		## borrowed this from BitTornado
		try:
			# metainfo_file = open(self.get_file_path_filename(), 'rb')
			metainfo_file = open(self.file_path.path, 'rb')
			metainfo	  = bdecode(metainfo_file.read())

			# note, this will only work for single file torrents which have the length key in the info dictionary
			info = metainfo['info']	   
			if info.has_key('length'):
				self.info_hash	  = sha(bencode(info)).hexdigest()
				self.piece_length = info['piece length']
				self.announce	  = metainfo['announce']
				self.size		  = info['length']
				self.name		  = info['name']
		except:
			raise

class Torrentclient(models.Model):
	torrents   = models.ManyToManyField(Torrent)
	ip		   = models.IPAddressField()
	port	   = models.IntegerField()
	peer_id	   = models.CharField(max_length=20)
	stopped	   = models.BooleanField(default = True)
	uploaded   = models.IntegerField(blank=True, null=True)
	downloaded = models.IntegerField(blank=True, null=True)
	left	   = models.IntegerField(blank=True, null=True)
	created	   = models.DateTimeField(blank=True, null=True)
	updated	   = models.DateTimeField(blank=True, null=True)

	def __unicode__(self):
		return "IP:%s:%d  Stopped:%s up:%d dn:%d rem:%d" % (self.ip, self.port, self.stopped, self.uploaded, self.downloaded, self.left)

	def addevent(self, values):
		if values['event'] == 'stopped':
			self.stopped = True
		else:
			self.stopped = False

		self.uploaded	= values['uploaded']
		self.downloaded = values['downloaded']
		self.left		= values['remaining']
