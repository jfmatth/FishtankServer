###
### admin.py - admin site registraiton.
###

from django.contrib import admin

from dtracker.models import Torrent

class TorrentAdmin(admin.ModelAdmin):
    list_display = ('name', 'info_hash', 'size')
    
admin.site.register(Torrent, TorrentAdmin)