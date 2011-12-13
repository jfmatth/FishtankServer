#from django import forms

from django.forms import ModelForm
from dtracker.models import Torrent

class TorrentUploadForm(ModelForm):
	class Meta:
		model = Torrent
		fields = ('file_path',)

