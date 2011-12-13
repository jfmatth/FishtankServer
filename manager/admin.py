from django.contrib import admin
from manager.models import ClientSetting, ManagedClient

admin.site.register(ClientSetting)
admin.site.register(ManagedClient)