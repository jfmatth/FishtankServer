# urls.py
from django.contrib.auth.decorators import login_required, permission_required
from django.conf.urls.defaults import patterns, url, include
from content.views import HomeView, PricingView, FaqView, AccountHomeView, AccountRestoreView, AccountZoneView, AccountFilterView, AccountDownloadView, AccountFileDirView

urlpatterns = patterns('',
    url(r'^home/', HomeView.as_view(), name="content_home"),
    url(r'^pricing/', PricingView.as_view(), name="content_pricing"),
    url(r'^faq/', FaqView.as_view(), name="content_faq"),
    url(r'^account/', login_required(AccountHomeView.as_view()), name="content_account"),
    url(r'^restore/', login_required(AccountRestoreView.as_view()), name="content_restore"),
    url(r'^zone/', login_required(AccountZoneView.as_view()), name="content_zone"),
    url(r'^filter/', login_required(AccountFilterView.as_view()), name="content_filter"),
    url(r'^download/', login_required(AccountDownloadView.as_view()), name="content_download"),
    url(r'^file_dir/', AccountFileDirView.as_view(), name="content_filedir"),
    #(r'^profile/', login_required(ProfileView.as_view())),    
)