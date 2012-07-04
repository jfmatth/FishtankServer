from django.db import models
from dtracker.models import Torrent

import uuid
import datetime

days2 = datetime.timedelta(days=2)

#public key support
from Crypto.PublicKey import RSA
from Crypto import Random

from django.contrib.auth.models import User

# returns new encryption keys.
def EncryptionKeys():
    # code from :http://www.laurentluce.com/posts/python-and-cryptography-with-pycrypto/
    print "Generating keys...Please Wait",
    random_generator = Random.new().read
    key = RSA.generate(2048, random_generator)  
    print "Done!"
    return key.exportKey(), key.publickey().exportKey()

"""
    Verification - records for registering new clients.  Generated each time a new EXE is gotten?
"""
class Verification(models.Model):
    verifykey = models.CharField(max_length=50, blank=True)
    company = models.ForeignKey(User)
    goodtill = models.DateField(blank=True)
    use_count = models.IntegerField(blank=True)

    def save(self, *args, **kwargs):
        # Generate various fields
        if self.id == None:
            # new record
            self.verifykey = str(uuid.uuid4() )
            self.goodtill  = datetime.datetime.today() + days2
            self.use_count = 0

        super(Verification,self).save(*args, **kwargs)

    """
    usekey() - Call when yu want to increment the number of uses a verification record has been used.
    """
    def usekey(self):
        self.use_count += 1
        self.save()

    def __unicode__(self):
        return "%s - %s - %s" % (self.company, self.verifykey, self.goodtill)


class ManagedClient(models.Model):
    hostname = models.CharField(max_length=100)
    macaddr = models.CharField(max_length=20)
    ipaddr = models.IPAddressField(blank=True, null=True)

    guid = models.CharField(max_length=50, blank=True)
    peerid = models.CharField(max_length=20, blank=True)
    
    privatekey = models.TextField()
    publickey = models.TextField()

    company = models.ForeignKey(User)

    verified = models.BooleanField()  # this client has been verified as being able to backup to / from cloud.

    # < moved over from Torrentclient>
    torrents   = models.ManyToManyField(Torrent, blank=True)
    
    port       = models.IntegerField(blank=True, null=True)
    stopped    = models.BooleanField(default = True)
    offered    = models.IntegerField(blank=True, null=True)
    uploaded   = models.IntegerField(blank=True, null=True)
    downloaded = models.IntegerField(blank=True, null=True)
    left       = models.IntegerField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # if the guid and/or peerID are blank, make new ones
        if self.id == None:            
            self.guid = str(uuid.uuid4() )
            self.peerid = (self.hostname + self.guid)[:20]

            # get our encryption keys.
            priv,pub = EncryptionKeys()
            self.privatekey = priv
            self.publickey = pub

        super(ManagedClient, self).save(*args, **kwargs)

    def __unicode__(self):
        return "%s.%s" % (self.company, self.hostname)

    def torrent_count(self):
        return self.torrents.all().count()


class DiskSpace(models.Model):
    """
    A record of disk space on a client
        diskcloud - How much are the cloud files using
        disksize  - How big is the whole disk
        diskfree  - How much free space is there.
        date      - When was this entry made (self updating).
    """
    cloud = models.IntegerField()
    size  = models.IntegerField()
    free  = models.IntegerField()
    date  = models.DateTimeField()
    
    client = models.ForeignKey(ManagedClient)

    def save(self, *args, **kwargs):
        # Generate various fields
        if self.id == None:
            # new record
            self.date = datetime.datetime.today()
        
        super(DiskSpace,self).save(*args, **kwargs)

    def backupsize(self):
        return self.free / 2 - self.cloud

    def __unicode__(self):
        return "Disk space s:%s c:%s f:%s - Max:%s" % (self.size, self.cloud, self.free, self.backupsize())


class ClientSetting(models.Model):
    name = models.CharField(max_length=20)
    value = models.CharField(max_length=50, blank=True)
    bigvalue = models.TextField(blank=True)
    
    client = models.ForeignKey(ManagedClient)
    
    def __unicode__(self):
        return "%s, %s = %s" %(self.client,self.name,self.value)

class Backup(models.Model):
    encryptkey = models.TextField()   # encrypted key of the zip file.
    fileuuid = models.CharField(max_length=50)
    date = models.DateTimeField( )
    torrent = models.OneToOneField(Torrent, null=True)
    
    client = models.ForeignKey(ManagedClient)
    
    def __unicode__(self):
        return "%s %s" % (self.client,self.date)
    
    def _filecount(self):
        return len(self.file_set.all() )
    
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
        return "%s" % self.fullpath