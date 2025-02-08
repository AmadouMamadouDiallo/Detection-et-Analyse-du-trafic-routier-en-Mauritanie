from django.urls import path
from . import views
from .views import stats_view, clear_history

urlpatterns = [
    path('index/', views.index, name='index'),
    path('', views.Acceuil, name='Acceuil'),
    path('upload-video/', views.upload_video, name='upload_video'),
    path('map/', views.map_view, name='map_view'),
    path('stats/', views.stats_view, name='stats'),
    path('api/traffic-data/', views.get_traffic_data, name='traffic_data'),
    path('clear-history/', clear_history, name='clear_history'),
]
