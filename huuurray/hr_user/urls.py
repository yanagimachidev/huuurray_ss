from django.urls import path
from huuurray.hr_user import views

app_name = 'hr_user'
urlpatterns = [
    path('upsert/', views.upsert, name='upsert'),
    path('imgupsert/', views.image_upsert, name='image_upsert'),
    path('getuser/', views.get_user_data, name='get_user_data'),
    path('ranking/', views.get_ranking, name='get_ranking'),
    path('follow/', views.follow_user, name='follow_user'),
    path('getflw/', views.get_follow_user, name='get_follow_user'),
]
