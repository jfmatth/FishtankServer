from django.db import models
from django.contrib.auth import models as auth_models
import datetime
from dtracker.bencode import bdecode, bencode
from hashlib import sha1

class TorrentCountManager(models.Manager):
	# returns a list of torrents that have less than 3 clients, hard coded 3 for now, will figure more out later.
	def get_query_set(self):
		return super(TorrentCountManager, self).get_query_set().extra( where = ['(select count(*) from dtracker_torrentclient_torrents where dtracker_torrent.id = dtracker_torrentclient_torrents.torrent_id) < 3'])

class Torrent(models.Model):
	name	  = models.CharField(max_length=200, blank=True)
	file_path = models.FileField("File location", upload_to='torrents', blank=True)
	info_hash = models.CharField("Info Hash", max_length=40, blank=True)
	uuid 	  = models.CharField("UUID", max_length=50, blank=True)
	size	  = models.IntegerField(blank=True, null=True)
	announce  = models.CharField("HTTP announce",max_length=100, blank=True)
	piece_length = models.IntegerField(blank=True, null=True)
	
	# standard and Custom manager for counting how many clients have this torrent.
	objects       = models.Manager()
	needclients   = TorrentCountManager()

	def __unicode__(self):
		return self.name
	
	def clientcount(self):
		return self.managedclient_set.all().count()
	
	def show_clients(self):
		s = ""
		for mc in self.managedclient_set.all():
			s += str(mc) + ", "
		return s
	
	# need to modify the save() routine to update the various fields, once the file is uploaded.
	def save(self):
		if self.id == None:
			# only calculate for new records.
			super(Torrent, self).save()
			
			self.fillin_torrent_fields()

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
				self.info_hash	  = sha1(bencode(info)).hexdigest()
				self.piece_length = info['piece length']
				self.announce	  = metainfo['announce']
				self.size		  = info['length']
				self.name		  = info['name']
		except:
			raise