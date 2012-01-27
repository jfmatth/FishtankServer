from django.db import models
from dtracker.models import Torrent

import uuid
import datetime

#public key support
from Crypto.PublicKey import RSA
from Crypto import Random


from django.contrib.auth.models import User

# returns new encryption keys.
def EncryptionKeys():
    # code from :http://www.laurentluce.com/posts/python-and-cryptography-with-pycrypto/
    print "Generating keys...Please Wait"
    random_generator = Random.new().read
    key = RSA.generate(2048, random_generator)  

    return key.exportKey(), key.publickey().exportKey()

class ManagedClient(models.Model):
    hostname = models.CharField(max_length=100)
    macaddr = models.CharField(max_length=20)
    ipaddr = models.IPAddressField(blank=True, null=True)

    guid = models.CharField(max_length=50, blank=True)
    peerid = models.CharField(max_length=50, blank=True)
    
    privatekey = models.TextField()
    publickey = models.TextField()

    company = models.ForeignKey(User)
    
    # < moved over from Torrentclient>
    torrents   = models.ManyToManyField(Torrent)
    port = models.IntegerField(blank=True, null=True)
    stopped       = models.BooleanField(default = True)
    offered    = models.IntegerField(blank=True, null=True)
    uploaded   = models.IntegerField(blank=True, null=True)
    downloaded = models.IntegerField(blank=True, null=True)
    left       = models.IntegerField(blank=True, null=True)

    def addevent(self, values):
        if values['event'] == 'stopped':
            self.stopped = True
        else:
            self.stopped = False

        self.uploaded    = values['uploaded']
        self.downloaded = values['downloaded']
        self.left        = values['remaining']
        self.ipaddr     = values['addr']
        self.port       = values['port']
        
    # </ moved over from Torrentclient>

    def save(self, *args, **kwargs):
        # if the guid and/or peerID are blank, make new ones
        if self.id == None:            
            self.guid = str(uuid.uuid4() )
            self.peerid = str(uuid.uuid4() ) 

            # get our encryption keys.
            priv,pub = EncryptionKeys()
            self.privatekey = priv
            self.publickey = pub

        super(ManagedClient, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.hostname
    
    
class ClientSetting(models.Model):
    name = models.CharField(max_length=20)
    value = models.CharField(max_length=50)
    
    client = models.ForeignKey(ManagedClient)
    
    def __unicode__(self):
        return "%s, %s = %s" %(self.client,self.name,self.value)

class Backup(models.Model):
    key = models.TextField()   # encrypted key of the zip file.
    filename = models.CharField(max_length=100)  # name of the .zip file in the cloud.
    date = models.DateTimeField(default=datetime.datetime.now() )
    
    client = models.ForeignKey(ManagedClient)
    
    def __unicode__(self):
        return "%s %s" % (self.client,self.date)
    
class File(models.Model):
    filename = models.CharField(max_length=100)
    fullpath = models.CharField(max_length=255)
    crc = models.CharField(max_length=50)
    size = models.IntegerField()
    moddate = models.DateTimeField()
    accdate = models.DateTimeField()
    createdate = models.DateTimeField()
    
    backup = models.ForeignKey(Backup)
    
    def __unicode__(self):
        return "%s\\%s" % (self.fullpath,self.filename)