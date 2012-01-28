###
### admin.py - admin site registraiton.
###

from django.contrib import admin

from dtracker.models import Torrent

class TorrentAdmin(admin.ModelAdmin):
    pass
    
admin.site.register(Torrent, TorrentAdmin)