from django.contrib import admin
from manager.models import ClientSetting, ManagedClient, Backup, File, Verification, DiskSpace, Restore, RestoreFile

class ClientAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'ipaddr', 'stopped', 'torrent_count')
admin.site.register(ManagedClient, ClientAdmin)

class ClientSettingAdmin(admin.ModelAdmin):
    list_filter = ('client',)
admin.site.register(ClientSetting, ClientSettingAdmin)


class FileInLine(admin.TabularInline):
    model = File
    readonly_fields = ("filename" , "fullpath", "crc")
    fields = ("filename", "fullpath", "crc")
    extra = 0
    can_delete = False 

class BackupAdmin(admin.ModelAdmin):
    list_display = ('date', 'client', 'fileuuid', '_filecount')


class FileAdmin(admin.ModelAdmin):
    list_filter = ('backup',)
    list_display = ('filename', 'size', 'fullpath')


class RestoreAdmin(admin.ModelAdmin):
    list_display = ("client","completed", )


admin.site.register(Restore, RestoreAdmin)
admin.site.register(RestoreFile)
    
admin.site.register(Backup, BackupAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(Verification)
admin.site.register(DiskSpace)
