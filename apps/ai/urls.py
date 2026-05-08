from django.urls import path
from . import views

app_name = 'ai'

urlpatterns = [
    path('chat/', views.chat, name='chat'),
    path('chat/clear/', views.chat_clear, name='chat_clear'),
]
