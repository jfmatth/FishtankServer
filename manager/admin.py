from django.contrib import admin
from manager.models import ClientSetting, ManagedClient, Backup, File

class ClientAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'ipaddr', 'stopped', 'torrent_count')
admin.site.register(ManagedClient, ClientAdmin)

admin.site.register(ClientSetting)

class BackupAdmin(admin.ModelAdmin):
    list_display = ('date', 'client', 'fileuuid', '_filecount')
    
admin.site.register(Backup, BackupAdmin)
admin.site.register(File)       