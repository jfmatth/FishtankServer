from django.contrib import admin
from manager.models import ClientSetting, ManagedClient, Backup, File, Verification

class ClientAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'ipaddr', 'stopped', 'torrent_count')
admin.site.register(ManagedClient, ClientAdmin)

admin.site.register(ClientSetting)

class FileInLine(admin.TabularInline):
    model = File
    readonly_fields = ("filename" , "fullpath", "crc")
    fields = ("filename", "fullpath", "crc")
    extra = 0
    can_delete = False 

class BackupAdmin(admin.ModelAdmin):
    list_display = ('date', 'client', 'fileuuid', '_filecount')
    

#    inlines = [
#              FileInLine,
#            ]
    
    
admin.site.register(Backup, BackupAdmin)
admin.site.register(File)
admin.site.register(Verification)