###
### admin.py - admin site registraiton.
###

from django.contrib import admin
from dtracker.models import Torrent

admin.site.register(Torrent)