from django.contrib import admin
from manager.models import ClientSetting, ManagedClient, Backup, File

admin.site.register(ClientSetting)
admin.site.register(ManagedClient)
admin.site.register(Backup)
admin.site.register(File)       