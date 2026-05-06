from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render


def home(request):
    return render(request, 'index.html')


urlpatterns = [
    path('', home, name='home'),
    path('catalog/', include('apps.catalog.urls')),
    path('library/', include('apps.library.urls')),
    path('admin/', admin.site.urls),
]
