from django.http import HttpResponse, HttpResponseBadRequest


from manager.models import ManagedClient, ClientSetting, Backup
from dtracker.models import Torrent

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count

import json
import anydbm
import os   
import datetime

GLOBALKEY = "__global__"

CLIENTEXE = "download\\client.exe"

DATETIMEFMT = "%m/%d/%Y %I:%M:%S %p"




class dbmForm(forms.Form):
    eKey = forms.CharField(max_length=700)
    guid = forms.CharField(max_length=50)
    dFile = forms.FileField()



def main(request):
    return HttpResponse('<a href="/manager/download/">Download client</a>')




def handledbm(ekey, guid, dbmfile):
    
    # first, find the client this data belongs to
    try:
        client = ManagedClient.objects.get(guid=guid)
    
        # save the file somewhere first
        destination = open('temp.dbm', 'wb+')
        for chunk in dbmfile.chunks():
            destination.write(chunk)
        destination.close()
        
        # add a record of this file in the DB
        newbackup = Backup()
        newbackup.key = ekey
        newbackup.filename = dbmfile.name
        newbackup.client = client
        newbackup.date = datetime.datetime.now()
        
        newbackup.save()
    
        # now add all the files from the DB as files under this backup.
        db = anydbm.open('temp.dbm', 'r')
        for key in db:
            d = json.loads(db[key])
            newbackup.file_set.create(
                filename = os.path.basename(d['filename']),
                fullpath = os.path.dirname(d['filename']),
                crc = d['crc'],
                size = d['size'],
                moddate = datetime.datetime.strptime(d['modified'],DATETIMEFMT),
                accdate = datetime.datetime.strptime(d['accessed'],DATETIMEFMT),
                createdate = datetime.datetime.strptime(d['created'],DATETIMEFMT)
            )
            
        return True
    except ObjectDoesNotExist:
        return False


def download(request):
    response = HttpResponse(open(CLIENTEXE,"rb").read())
    response['Content-Type']='application/force-download'
    response['Content-disposition'] = 'attachment; filename=%s' % CLIENTEXE
    return response 

def dbmupload(request):
    if request.method == 'POST':
        form = dbmForm(request.POST, request.FILES)
        if form.is_valid():
            if handledbm(request.POST['eKey'],request.POST['guid'], request.FILES['dFile']):
                return HttpResponse("valid")
            else:
                return HttpResponse("Unable to injest")
        else:
            return HttpResponse("something bad")
    else:
            return HttpResponse("GET no good here")

    
def register(request):

    returnstr = ""
    
    # validate the user ID and password
    try:
        user = User.objects.get(pk=request.POST['userid'])
        
        if not user.check_password(request.POST['password']):
            return HttpResponseBadRequest("Unable to login")
        
    except ObjectDoesNotExist:
        return HttpResponseBadRequest("Unable to login")

    # try to find this client on the list of managed clients.
    # user should have our user object, we need to see if our hostname + macaddr combo is here or not, if
    # not, add it and generate a GUID and PEERID setting.
    try:
        mc = user.managedclient_set.get(hostname__exact = request.POST['hostname'],
                                        macaddr__exact  = request.POST['macaddr'] )
    except ObjectDoesNotExist:
        mc = user.managedclient_set.create(hostname=request.POST['hostname'],
                                           macaddr = request.POST['macaddr'],
                                           )

    # we are going to return a JSON object now :)
    body = json.dumps({'guid':mc.guid, 'publickey':mc.publickey, 'returnstr':returnstr} )
    
    return HttpResponse(body)
    
def setting(request, guid, setting):
    # allows for reading and writing 
    if request.method == 'GET':
        # requesting a setting
        
        # check to see if we are asking for a client field value with # in the name?
        if setting[0] == "_":
            try:
                client = ManagedClient.objects.get(guid__exact=guid)
                
                # go through all the client's fields, and see if we find a match
                fieldname = setting[1:]
                return HttpResponse( getattr(client,fieldname) )
            except:
                return HttpResponseBadRequest("%s not found" % setting)
        else:      
            try:
                value = ClientSetting.objects.get(client__guid__exact=guid,
                                                  name__exact=setting).value
                return HttpResponse(value)
            except ObjectDoesNotExist:
                # Check for global variables.
                try:
                    value = ClientSetting.objects.get(client__guid__exact=GLOBALKEY,
                                                      name__exact=setting).value
                    return HttpResponse(value)
                except:
                    return HttpResponseBadRequest("Key Not found")
        
    if request.method == 'POST':
        if guid == GLOBALKEY:
            return HttpResponseBadRequest("Can't update %s values" % GLOBALKEY)
        
        # they want to save a value
        if "value" not in request.POST:
            return HttpResponseBadRequest("No value parameter specified")
        
        try:
            # see if setting already exists, if so, get the record and we'll update that.
            thesetting = ClientSetting.objects.get(client__guid__exact=guid, 
                                                   name__exact=setting)            
        except ObjectDoesNotExist:
            # find the client first
            try:
                theclient = ManagedClient.objects.get(guid__exact=guid)
            except:
                return HttpResponseBadRequest("client key not found")
            
            # now setup a new client setting value.
            thesetting = ClientSetting(client=theclient)
            thesetting.name = setting
        
        # update / save our setting
        try:
            thesetting.value = request.POST['value']
            thesetting.save()
            return HttpResponse(thesetting.value)
        except:
            return HttpResponseBadRequest("Can't save value")

# asking the server for what torrents there are to be backed up from the cloud.
def getcloud(request):
    if not request.GET.has_key("size"):
        return HttpResponseBadRequest("no size sent")
        
    if not request.GET.has_key("guid"):
        return HttpResponseBadRequest("no GUID sent")
    
#    >>> Torrent.objects.exclude(managedclient__guid="5dc71a04-154c-4ed0-ad4d-376cd03
#96731").annotate(tc=Count('managedclient')).filter(tc__lt=2)
    
    # so find all torrents that are less in size than 'size' and return the first one to the client.
    tl = Torrent.objects.annotate(tc=Count("managedclient")).filter(tc__lt=2)
    if len(tl)>0 :
        return HttpResponse(tl[0].info_hash)
