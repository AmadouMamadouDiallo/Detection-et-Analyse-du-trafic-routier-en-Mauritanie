from django.db import models

class TrafficData(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    vehicle_count = models.IntegerField(default=0)
    congestion_level = models.FloatField(default=0.0)
    latitude = models.FloatField()
    longitude = models.FloatField()
    video_source = models.CharField(max_length=255)

    def __str__(self):
        return f"Traffic Data at {self.timestamp}"

class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('car', 'Car'),
        ('truck', 'Truck'),
        ('bus', 'Bus'),
        ('motorcycle', 'Motorcycle'),
    ]
    
    traffic_data = models.ForeignKey(TrafficData, on_delete=models.CASCADE)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    trajectory = models.JSONField()  # Stocke les coordonnées du trajet
    detection_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle_type} detected at {self.detection_time}"
