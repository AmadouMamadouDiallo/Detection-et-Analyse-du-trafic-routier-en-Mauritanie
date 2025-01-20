from django.urls import path
from . import views

urlpatterns = [
    path('analyze/', views.index, name='index'),
    path('map/', views.map_view, name='map_view'),
    path('stats/', views.stats_view, name='stats'),
    path('', views.analyze_local_video, name='analyze_local_video'),
    path('api/process-video/', views.process_video, name='process_video'),
    path('api/traffic-data/', views.get_traffic_data, name='traffic_data'),
]
