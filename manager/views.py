import user
from django.http import HttpResponse, HttpResponseBadRequest

from manager.models import ManagedClient, ClientSetting, Backup, Verification, DiskSpace, Restore, RestoreFile
from dtracker.models import Torrent

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.shortcuts import get_object_or_404

import json
import anydbm
import os   
import datetime
import urllib

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

    uploaddbm = 'injest/' + rPOST['backupguid']
    
    clientguid = rPOST['clientguid']
    ekey = rPOST['eKey']
    
    # first, find the client this data belongs to
    try:
        client = ManagedClient.objects.get(guid=clientguid)

        dbmfile = rFILES['dFile']
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
                s = ClientSetting.objects.get(client__guid__exact=guid,
                                              name__exact=setting)
                                                  
                # try the value field, otherwise get the bigvalue field.
                return HttpResponse(s.value or s.bigvalue)
            
            except ObjectDoesNotExist:
                # Check for global variables.
                try:
                    s = ClientSetting.objects.get(client__guid__exact=GLOBALKEY,
                                                  name__exact=setting)
                    return HttpResponse(s.value or s.bigvalue)
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


def validclient(request):
    # 
    return HttpResponse("valid client check")

def ping(request):
    """
    A simple view to see if the server is alive.  Requires a client guid to be passed in, and if the 
    manager is online and the guid is valid, an OK is sent, otherwise various bad request text's are sent back.
    """
    if 'guid' in request.GET:
        guid=request.GET['guid'] 
        try:
            ManagedClient.objects.get(guid__exact=guid)
            return HttpResponse("OK")
        except ObjectDoesNotExist:
            return HttpResponseBadRequest("not registered")
    else:
        return HttpResponseBadRequest("NO GUID")


def diskspace(request):
    """
    A view to update the DiskSpace record for this client.
    
    Information is sent to update the diskspace table, and in return, we'll give you what Infohash's can be backed up.
    """
    if request.POST:
        if not ("guid" in request.POST and "cloud" in request.POST and "size" in request.POST and "free" in request.POST):
            return HttpResponseBadRequest("Missing guid, cloud, size or free")
        
        # find the client and update the
        try: 
            client = ManagedClient.objects.get( guid__exact=request.POST["guid"] )
            
            ds = DiskSpace()
            ds.client = client
            ds.cloud = int(request.POST["cloud"])
            ds.size  = int(request.POST["size"])
            ds.free  = int(request.POST["free"])
            ds.save()
        
            # now figure out who needs to be backed up.
            try:
                # so we can backup a maximum of 50% free space, subtract the cloud usage, and what remains is what we can then use.
                maxsize = ds.free / 2 - ds.cloud
                if maxsize > 0:
                    
                #    Only return torrents which this client isn't already hosting and other filters / exclusions.
                    tl = Torrent.objects.filter(managedclient__company=client.company,
                                                managedclient__stopped=False,
                                                size__lt=int(maxsize),
                                                managedclient__verified=True,
                                                )\
                                        .exclude(managedclient__guid=request.POST['guid'])\
                                        .annotate(tc=Count('managedclient')).filter(tc__lt=3)
                
                    if len(tl)>0 :
                        return HttpResponse(tl[0].info_hash)
                    else:
                        return HttpResponse("")
                else:
                        return HttpResponse("")
            except:
                return HttpResponseBadRequest("Error calculating maxsize")
            
        except ObjectDoesNotExist:
            return HttpResponseBadRequest("Client not found")
    else:
        return HttpResponseBadRequest("No Get response")


def restore(request, guid):
    """
    Given a client GUID it returns a JSON string of all files restored, and each of their coorepsonding torrent infohashes.
    """
    #lookup the client first
    c = get_object_or_404(ManagedClient, guid__exact=guid)        
    
    if request.method == "GET":
        # GET to check if there are any restores needed
        r = Restore.objects.all().\
                filter(client=c, completed=False).\
                order_by("requested")
        
        if len(r) > 0:
            # only return the restores for this request.
            rl = r[0].restorefile_set.all().order_by("file__backup__torrent__info_hash")
            
            # rl now has all the restores to be done, so return them as a JSON file
            #
            # return down a dictionary by infohash for every file in that infohash that should be
            # restored, including the record ID  

            RestoreDict = {}
            RestoreDict = {"id": r[0].id,
                           'restores':{}}
            for l in rl:
                if not l.file.backup.torrent.info_hash in RestoreDict['restores']:
                    RestoreDict['restores'][l.file.backup.torrent.info_hash]  = {'key': l.file.backup.encryptkey,
                                                                    'zipfile': l.file.backup.torrent.name,
                                                                    'files':[] }
                # use .append() instead of +=
                RestoreDict['restores'][l.file.backup.torrent.info_hash]['files'].append( (l.file.fullpath+"\\"+l.file.filename, l.file.id) )

            # now we have a dict of what we want, just JSON it and return it
            return HttpResponse( json.dumps(RestoreDict) )
        else:
            return HttpResponse("no records", status=204)
    
    elif request.method=="POST":
        print request.POST
        
        if "restore" in request.POST and "status" in request.POST:
            # we are posting back the status of the restore job, restore is the ID of the job
            try:
                id = request.POST["restore"]
                r = Restore.objects.get(pk=id)
                if request.POST["status"] == "complete":
                    r.completed = True
                    r.save()
                    
#                return HttpResponse("Posted")
            except:
#                return HttpResponse("Error")
                pass
        
        if "file" in request.POST and "status" in request.POST:
                id = request.POST["file"]
                r = RestoreFile.objects.get(pk=id)
                if request.POST["status"] == "complete":
                    r.completed = True
                    r.save()
                    
                print "Updated the File record"
#                return HttpResponse("Posted")

        return HttpResponse("POST CODE")
                    
    
    