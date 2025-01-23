from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload-video/', views.upload_video, name='upload_video'),
    path('map/', views.map_view, name='map_view'),
    path('stats/', views.stats_view, name='stats'),
    path('api/traffic-data/', views.get_traffic_data, name='traffic_data'),
]
