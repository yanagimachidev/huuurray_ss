from django.urls import path
from huuurray.hr_sp import views

app_name = 'hr_sp'
urlpatterns = [
    path('upsert/', views.upsert, name='upsert'),
    path('getpoint/', views.get_point, name='get_point')
]
