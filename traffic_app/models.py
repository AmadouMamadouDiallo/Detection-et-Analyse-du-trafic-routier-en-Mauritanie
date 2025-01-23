from django.db import models
from django.utils import timezone

class VideoUpload(models.Model):
    video_file = models.FileField(upload_to='uploads/')
    upload_date = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    location = models.CharField(max_length=255, default="Nouakchott, Mauritanie")
    vehicle_count = models.IntegerField(default=0)
    congestion_level = models.FloatField(default=0.0)
    processing_time = models.FloatField(default=0.0)  # en secondes
    status = models.CharField(max_length=50, default='pending')
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Vidéo {self.id} - {self.upload_date.strftime('%d/%m/%Y %H:%M')}"

class TrafficData(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    vehicle_count = models.IntegerField(default=0)
    congestion_level = models.FloatField(default=0.0)
    latitude = models.FloatField(default=18.0735)  # Coordonnées par défaut de Nouakchott
    longitude = models.FloatField(default=-15.9582)
    video_source = models.CharField(max_length=255)
    location_name = models.CharField(max_length=255, default="Nouakchott")
    weather_condition = models.CharField(max_length=100, blank=True, default="")
    temperature = models.FloatField(null=True, blank=True)
    peak_hour = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Trafic à {self.location_name} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"

class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('car', 'Voiture'),
        ('truck', 'Camion'),
        ('bus', 'Bus'),
        ('motorcycle', 'Moto'),
    ]
    
    traffic_data = models.ForeignKey(TrafficData, on_delete=models.CASCADE, related_name='vehicles')
    vehicle_type = models.CharField(max_length=50, choices=VEHICLE_TYPES, default='car')
    detection_time = models.DateTimeField(auto_now_add=True)
    confidence_score = models.FloatField(default=0.0)
    trajectory = models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.vehicle_type} détecté le {self.detection_time.strftime('%d/%m/%Y %H:%M')}"
