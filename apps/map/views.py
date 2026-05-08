from django.shortcuts import render
from django.conf import settings

TWOGIS_KEY = settings.TWOGIS_API_KEY


def map_index(request):
    return render(request, 'map/index.html', {'twogis_key': TWOGIS_KEY})
