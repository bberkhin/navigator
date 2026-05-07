from django.shortcuts import render
from django.conf import settings

TWOGIS_KEY = getattr(settings, 'TWOGIS_API_KEY', '55ddd2c7-9163-437f-b597-82db36fac025')


def map_index(request):
    return render(request, 'map/index.html', {'twogis_key': TWOGIS_KEY})
