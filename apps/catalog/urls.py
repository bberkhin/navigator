from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.catalog_list, name='list'),
    path('<slug:slug>/', views.catalog_detail, name='detail'),
]
