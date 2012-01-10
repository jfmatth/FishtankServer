from django.http import HttpResponse, HttpResponseBadRequest

from django import forms

from manager.models import ManagedClient, ClientSetting, Backup, File
from django.contrib.auth.models import User

from django.core.exceptions import ObjectDoesNotExist

import json
import anydbm
import os
import datetime

GLOBALKEY = "__global__"

CLIENTEXE = "client.exe"

DATETIMEFMT = "%m/%d/%Y %I:%M:%S %p"

class dbmForm(forms.Form):
    eKey = forms.CharField(max_length=700)
    guid = forms.CharField(max_length=50)
    dFile = forms.FileField()


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

def main(request):
    return HttpResponse("Nothing yet")

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
    
    try:
    
        returnstr = "Here's what u sent me:"
        if 'user' in request.POST:
            returnstr += request.POST['user']
        if 'password' in request.POST:
            returnstr += request.POST['password']
        if 'macaddr' in request.POST:
            returnstr += request.POST['macaddr']
        if 'ipaddr' in request.POST:
            returnstr += request.POST['ipaddr']
        if 'hostname' in request.POST:
            returnstr += request.POST['hostname']
    
        # validate the user ID and password
        try:
            user = User.objects.get(pk=request.POST['user'])
            
            if user.check_password(request.POST['password']):
                returnstr += "Logged in successfully "
            else:
                returnstr += "Failed Login "
        except:
            returnstr += "Exception on finding user "
    
        # try to find this client on the list of managed clients.
        # user should have our user object, we need to see if our hostname + macaddr combo is here or not, if
        # not, add it and generate a GUID and PEERID setting.
        try:
            mc = user.managedclient_set.get(hostname__exact = request.POST['hostname'],
                                            macaddr__exact  = request.POST['macaddr'] )
            returnstr += "found client "
        except ObjectDoesNotExist:
            mc = user.managedclient_set.create(hostname=request.POST['hostname'],
                                               macaddr = request.POST['macaddr'],
                                               )
            returnstr += "creating client "

    finally:
        returnstr += mc.hostname

        # we are going to return a JSON object now :)
        body = json.dumps({'guid':mc.guid, 'publickey':mc.publickey, 'returnstr':returnstr} )
    
        return HttpResponse(body)
    
def setting(request, guid, setting):
    # allows for reading and writing 
    if request.method == 'GET':
        # requesting a setting
        
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
        