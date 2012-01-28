from django.contrib import admin
from manager.models import ClientSetting, ManagedClient, Backup, File

class ClientAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'stopped', 'torrent_count')

admin.site.register(ClientSetting)
admin.site.register(ManagedClient, ClientAdmin)
admin.site.register(Backup)
admin.site.register(File)       