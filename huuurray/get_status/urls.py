from django.urls import path
from huuurray.get_status import views

app_name = 'get_status'
urlpatterns = [
    path('index/', views.send_status, name='send_status'),
]
