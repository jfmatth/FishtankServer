# Create your views here.
from django.views.generic import View, TemplateView
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from manager.models import *

#def HomeView(request):
#    template_name = "web/home.html"
#    

from django.shortcuts import redirect
from django.shortcuts import render_to_response
from django.template import RequestContext

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
    
        import urllib, os    
        #self.context['somecrap'] = "this is a test of context"
        
        print request.user
        
        if dir in request.POST: 
            get_hosts = False
            dir = request.POST['dir']
        else: 
            get_hosts = True
        
        r=['<ul class="jqueryFileTree" style="display: none;">']
        
        if get_hosts:
            hosts = ManagedClient.objects.filter(company__username=request.user.username)
            for h in hosts:
                r.append('<li class="directory collapsed"><a href="#" rel="%s/">%s</a></li>' % (h,h))
        else:        
        
            try:
                r=['<ul class="jqueryFileTree" style="display: none;">']
                d=urllib.unquote(request.POST.get('dir','c:\\temp'))
                for f in os.listdir(d):
                    ff=os.path.join(d,f)
                    if os.path.isdir(ff):
                        r.append('<li class="directory collapsed"><a href="#" rel="%s/">%s</a></li>' % (ff,f))
                    else:
                        e=os.path.splitext(f)[1][1:] # get .ext and remove dot
                        r.append('<li class="file ext_%s"><a href="#" rel="%s">%s</a></li>' % (e,ff,f))
                r.append('</ul>')
            except Exception,e:
                r.append('Could not load directory: %s' % str(e))
        r.append('</ul>')
        return HttpResponse(r)
        #return render_to_response('content/account/file_dir.html', {'stuff': "this is a test of context"})
