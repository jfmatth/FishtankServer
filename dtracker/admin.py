###
### admin.py - admin site registraiton.
###

from django.contrib import admin
from mserver.dtracker.models import Torrent, Torrentclient

class TorrentClientInline(admin.StackedInline):
	model = Torrentclient


class TorrentAdmin(admin.ModelAdmin):
	inlines = [TorrentClientInline]

admin.site.register(Torrent)
admin.site.register(Torrentclient)