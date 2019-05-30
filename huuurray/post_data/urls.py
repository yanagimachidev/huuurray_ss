from django.urls import path
from huuurray.post_data import views

app_name = 'post_data'
urlpatterns = [
    path('upsert/', views.upsert, name='upsert'),
    path('getpost/', views.get_post_data, name='get_post_data'),
    path('nice/', views.nice, name='nice'),
    path('getnice/', views.get_nice, name='get_nice')
]
