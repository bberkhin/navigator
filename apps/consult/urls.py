from django.urls import path
from . import views

app_name = 'consult'

urlpatterns = [
    path('', views.consult_index, name='index'),
]
