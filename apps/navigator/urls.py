from django.urls import path
from . import views

app_name = 'navigator'

urlpatterns = [
    path('', views.navigator_index, name='index'),
    path('ai/', views.navigator_ai, name='ai'),
    path('anketa/', views.navigator_anketa, name='anketa'),
]
