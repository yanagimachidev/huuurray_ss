from django.urls import path
from huuurray.hr_message import views

app_name = 'hr_message'
urlpatterns = [
    path('upsert/', views.upsert, name='upsert'),
    path('getmessage/', views.get_message, name='get_message'),
    path('getmessagefeed/', views.get_message_feed, name='get_message_feed'),
    path('nice/', views.nice, name='nice'),
    path('getnice/', views.get_nice, name='get_nice')
]
