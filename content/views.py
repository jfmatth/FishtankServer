from django.views.generic import View, TemplateView
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from manager.models import *
from django.db.models import Q
import urllib, os
from django.utils import simplejson

from django.shortcuts import redirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from sets import Set

# Public views
class HomeView(TemplateView):
    template_name = "content/home.html"
    success_url = "/"

class FaqView(TemplateView):
    template_name = "content/faq.html"
    success_url = "/"

class PricingView(TemplateView):
    template_name = "content/pricing.html"
    success_url = "/"
    
# Account specific views
class AccountHomeView(TemplateView):
    template_name = "content/account/home.html"
    success_url = "/"

class AccountRestoreView(TemplateView):
    template_name = "content/account/restore.html"
    success_url = "/"

class AccountFilterView(TemplateView):
    template_name = "content/account/filter.html"
    success_url = "/"
    
class AccountZoneView(TemplateView):
    template_name = "content/account/zone.html"
    success_url = "/"
    
class AccountDownloadView(TemplateView):
    template_name = "content/account/download.html"
    success_url = "/"

class AccountFileDirView(TemplateView):
    template_name = "content/account/file_dir.html"
    success_url = "/"
    
    def post(self, request, *args, **kwargs):
        
        #self.context['somecrap'] = "this is a test of context"
        
        try:
            print "getting directories..."
                        
            if request.POST['dir']:
                get_hosts = False
                dir = request.POST['dir']
            else:
                print "getting hosts..."
                get_hosts = True
        except Exception,e:
            return HttpResponse('Could not load directory: %s' % str(e))
        
        
        r=['<ul class="jqueryFileTree" style="display: none;">']
        
        if get_hosts:
            hosts = ManagedClient.objects.filter(company__username=request.user.username)
            for h in hosts:
                r.append('<li class="directory collapsed"><a href="#" class="%s" rel="%s">%s</a></li>' % (h.hostname, "c:/",h.hostname))
            r.append('</ul>')
        else:        
            try:
                
                print 'getting files....'
                r=['<ul class="jqueryFileTree" style="display: none;">']
                dirpath = urllib.unquote(request.POST.get('dir'))
                hostname= urllib.unquote(request.POST.get('host'))
                
                # dirpath - c:\\dir1\\subdir1, c:\\
                # relpath - dir1\\subdir1, \\             
                
                print "your directory", dirpath, repr(dirpath), str(dirpath)
                print "your host", hostname
                
                # deal with the backslash on the root "c:\" drives
                if os.path.normpath(dirpath) == os.path.normpath('c:/'):  #'c:\\\\':
                    print "setting up regex for root"
                    f_regex = dirpath + r"$"
                    #d_regex = dirpath + r"[^\\]+\\.+$"
                    # original d_regex was not picking up all directories...
                    d_regex = dirpath + r"[^/]+(/.+)*$"          
                
                else:              
                    print "setting up regex for subtree"
                    f_regex = dirpath + "$"
                    #d_regex = dirpath + r"\\[^\\]+\\.+$"
                    # original d_regex was not picking up all directories...
                    d_regex = dirpath + r"/[^/]+(/.+)*$"
                    dirpath = dirpath + "/"
                
                print "f_regex", f_regex
                print "d_regex", d_regex
                
                s=set()
                               
                # returns dicts
                # I can't put files and directories into the same query, because the returned objects differ.
                # So we break them out like so...
                directories = File.objects.filter( Q(backup__client__hostname=hostname) &  Q(fullpath__regex=d_regex) ).values("fullpath").distinct()
                for d in directories:
                    #print "stripping", os.path.normpath(dirpath), "from ", d['fullpath']
                    dir_prefix = d['fullpath'][len(os.path.normpath(dirpath)):]
                    #print "prefix ", dir_prefix
                    dir_prefix = dir_prefix.lstrip("/")
                    #print "stripped prefix ", dir_prefix
                    
                    dir_prefix = dir_prefix.split("/", 1)[0]
                    
                    #print "prefix", dir_prefix
                    s.add(dir_prefix)
                    
                print "your top level directories"
                for i in s:
                    print i
                print "end top level directories"
                    
                
                # returns File objects
                files = File.objects.filter( Q(backup__client__hostname=hostname) & Q(fullpath__regex=f_regex) )
                for f in files:
                    print f
                
                #for d in directories:
                #    r.append('<li class="directory collapsed"><a href="#" rel="%s">%s</a></li>' % (d,os.path.basename(d)))
                
                for f in files:
                    e=os.path.splitext(f.filename)[1][1:] # get .ext and remove dot
                    r.append('<li class="file ext_%s"><a href="#" class="%s" rel="%s" id="%s">%s</a></li>' % (e,
                                                                                                      hostname,
                                                                                                      os.path.normpath(f.fullpath + f.filename),
                                                                                                      f.id,
                                                                                                      f.filename))
                
                
                for d in s:
                    r.append('<li class="directory collapsed"><a href="#" class="%s" rel="%s">%s</a></li>' % (hostname,
                                                                                                              dirpath + d,
                                                                                                              os.path.basename(d))) 
                
                r.append('</ul>')
            except Exception,e:
                r.append('Could not load directory: %s' % str(e))
        return HttpResponse(r)

class AccountFileRestoreView(TemplateView):
    """
    Files checked out for restore.
    """
    template_name = "content/account/file_checkout.html"
    success_url = "/"
    
    def post(self, request, *args, **kwargs):
             
        print "I'm here!"
        print request.raw_post_data
        print "after"
        post_data = simplejson.loads(request.raw_post_data)
        
        hosts = post_data['files']
        restores = []
        
        try:
            for host, files in hosts.items():
                print host
                client = ManagedClient.objects.get(hostname=host)
            
                # Right now client and restoreclient are the same thing. :)
                restore = Restore(client=client, retoreclient=client, requested=datetime.datetime.now(), completed=False, status="R")
                restore.save()
                
                #restore_set = Set()                
                for file in files:
                    print "fileid: ", file
                    file = File.objects.get(id=file)
                    restore_file = RestoreFile(restore=restore, file=file, status="R", completed=False)
                    restore_file.save()
        except Exception, e:
            print e

        
        #print files['tbackup1']
        
        #for file in post_data['files']:
            #print file


        #if request.POST['one']:
        #    print "worked"
        #else:
        #    print "did not work"
        
        return HttpResponse("What!  Here's your returned data.")

