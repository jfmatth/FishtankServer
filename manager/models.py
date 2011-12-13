from django.db import models

import uuid

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
