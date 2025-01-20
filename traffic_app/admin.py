from django.contrib import admin
from .models import TrafficData, Vehicle

@admin.register(TrafficData)
class TrafficDataAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'vehicle_count', 'congestion_level', 'latitude', 'longitude')
    list_filter = ('timestamp',)
    search_fields = ('video_source',)

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_type', 'detection_time', 'traffic_data')
    list_filter = ('vehicle_type', 'detection_time')
    search_fields = ('vehicle_type',)
