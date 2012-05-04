import user
from django.http import HttpResponse, HttpResponseBadRequest

from manager.models import ManagedClient, ClientSetting, Backup, Verification
from dtracker.models import Torrent

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q

import json
import anydbm
import os   
import datetime

GLOBALKEY = "__global__"

CLIENTEXE = "download\\client.exe"

DATETIMEFMT = "%m/%d/%Y %I:%M:%S %p"

class dbmForm(forms.Form):
    eKey = forms.CharField(max_length=700)
    clientguid = forms.CharField(max_length=50)
    backupguid = forms.CharField(max_length=50)
    dFile = forms.FileField()

def main(request):
    return HttpResponse('<a href="/manager/download/">Download client</a>')

def handledbm(rPOST, rFILES):

#    uploaddbm = 'injest/temp.dbm'    
    uploaddbm = 'injest/' + rPOST['backupguid']
    
    clientguid = rPOST['clientguid']
    ekey = rPOST['eKey'] 
    
    # first, find the client this data belongs to
    try:
        client = ManagedClient.objects.get(guid=clientguid)

        dbmfile = rFILES['dFile']
        ekey
        # save the file somewhere first
        destination = open(uploaddbm, 'wb+')
        for chunk in dbmfile.chunks():
            destination.write(chunk)
        destination.close()
        
        # add a record of this file in the DB
        newbackup = Backup()
        newbackup.encryptkey = ekey
        newbackup.fileuuid = dbmfile.name.split(".")[0]  
        newbackup.client = client
        newbackup.date = datetime.datetime.now()

        newbackup.save()

        # now add all the files from the DB as files under this backup.
        db = anydbm.open(uploaddbm, 'r')
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

        db.close()
        os.remove(uploaddbm)

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
            if handledbm(request.POST,request.FILES):
                return HttpResponse("valid")
            else:
                return HttpResponse("Unable to injest")
        else:
            return HttpResponse("something bad")
    else:
            return HttpResponse("GET no good here")

    
def register(request):

    returnstr = ""

    missinginfo = False

    # validate all our settings
    if not "verifykey" in request.POST:
        missinginfo = True
    if not "hostname" in request.POST:
        missinginfo = True
    if not "macaddr" in request.POST:
        missinginfo = True
    if not "ipaddr" in request.POST:
        missinginfo = True

    if missinginfo:
        return HttpResponseBadRequest("Unable to register")

# JFM, change way we register, not with ID / Password anymore, use the verification table.
#    # validate the user ID and password
#    try:
#        user = User.objects.get(pk=request.POST['userid'])
#
#        if not user.check_password(request.POST['password']):
#            return HttpResponseBadRequest("Unable to login")
#
#    except ObjectDoesNotExist:
#        return HttpResponseBadRequest("Unable to login")

    # try to find the verifykey and see if it's OK.
    try:
        k = Verification.objects.get(verifykey = request.POST['verifykey'])
        # key was found, make sure it's not expired

#        if datetime.date.today() > k.goodtill:
#            return HttpResponseBadRequest("Unable to register, key expired")

        # key is found and not expired, bonus!

        # set the user record
        user = k.company

    except ObjectDoesNotExist:
        return HttpResponseBadRequest("Unable to register, unknown key")

    # try to find this client on the list of managed clients.
    # user should have our user object, we need to see if our hostname + macaddr combo is here or not, if
    # not, add it and generate a GUID and PEERID setting.
    try:
        #mc = user.managedclient_set.get(hostname__exact = request.POST['hostname'],
        #                                macaddr__exact  = request.POST['macaddr'] )
        mc = user.managedclient_set.get(hostname__exact = request.POST['hostname'] )
        
        mc.ipaddr = request.POST['ipaddr']
        mc.save()
        
    except ObjectDoesNotExist:
        mc = user.managedclient_set.create(hostname=request.POST['hostname'],
                                           macaddr = request.POST['macaddr'],
                                           ipaddr = request.POST['ipaddr']
                                           )

    k.usekey()

    # we are going to return a JSON object now :)
    body = json.dumps( {'guid':mc.guid,
                        'publickey':mc.publickey,
                        'privatekey':mc.privatekey,
                        'returnstr':returnstr} )

    return HttpResponse(body)
    
def setting(request, guid, setting):
    # allows for reading and writing 
    if request.method == 'GET':
        # check to make sure this is a valid client
        try:
            client = ManagedClient.objects.get(guid__exact=guid)
        except ObjectDoesNotExist:
            return HttpResponseBadRequest("not registered")

        # check to see if we are asking for a client field value with # in the name?
        if setting[0] == "_":
            try:
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
        

# asking the server for what torrents there are to be backed up from the cloud.
def getcloud(request):  
    if not request.GET.has_key("size"):
        return HttpResponseBadRequest("no size sent")
        
    if not request.GET.has_key("guid"):
        return HttpResponseBadRequest("no GUID sent")
        
#    qTorrentExclude = Q(managedclient__guid=request.GET['guid'])
#    qTorrentFilter = Q(managedclient__stopped=False,size__lt = int(request.GET['size']) )
        
    # find the user / company that's requesting, so we only offer torrents of that company
    company = ManagedClient.objects.get(guid=request.GET["guid"]).company

#    Only return torrents which this client isn't already hosting and other filters / exclusions.
    tl = Torrent.objects.filter(managedclient__company=company,
                                managedclient__stopped=False,
                                size__lt=int(request.GET['size']),
                                managedclient__verified=True,
                                )\
                        .exclude(managedclient__guid=request.GET['guid'])\
                        .annotate(tc=Count('managedclient')).filter(tc__lt=3)
#    tl = Torrent.objects.exclude(qTorrentExclude).annotate(tc=Count('managedclient')).filter(tc__lt=3)

    if len(tl)>0 :
        return HttpResponse(tl[0].info_hash)
    else:
        return HttpResponse("")
