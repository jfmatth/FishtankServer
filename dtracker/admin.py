###
### admin.py - admin site registraiton.
###

from django.contrib import admin

from dtracker.models import Torrent

class TorrentAdmin(admin.ModelAdmin):
    list_display = ('name', 'info_hash', 'clientcount',)
    
    fields = ['name', 'info_hash', 'show_clients', 'size']
    readonly_fields = ('show_clients',)
    
admin.site.register(Torrent, TorrentAdmin)