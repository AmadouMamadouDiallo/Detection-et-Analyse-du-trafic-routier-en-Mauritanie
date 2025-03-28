# Generated by Django 5.0 on 2025-01-23 16:06

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('traffic_app', '0002_videoupload'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='trafficdata',
            options={'ordering': ['-timestamp']},
        ),
        migrations.RenameField(
            model_name='videoupload',
            old_name='uploaded_at',
            new_name='upload_date',
        ),
        migrations.AddField(
            model_name='trafficdata',
            name='location_name',
            field=models.CharField(default='Nouakchott', max_length=255),
        ),
        migrations.AddField(
            model_name='trafficdata',
            name='peak_hour',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='trafficdata',
            name='temperature',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='trafficdata',
            name='weather_condition',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='vehicle',
            name='confidence_score',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='videoupload',
            name='congestion_level',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='videoupload',
            name='error_message',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='videoupload',
            name='location',
            field=models.CharField(default='Nouakchott, Mauritanie', max_length=255),
        ),
        migrations.AddField(
            model_name='videoupload',
            name='processing_time',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='videoupload',
            name='status',
            field=models.CharField(default='pending', max_length=50),
        ),
        migrations.AddField(
            model_name='videoupload',
            name='vehicle_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='trafficdata',
            name='latitude',
            field=models.FloatField(default=18.0735),
        ),
        migrations.AlterField(
            model_name='trafficdata',
            name='longitude',
            field=models.FloatField(default=-15.9582),
        ),
        migrations.AlterField(
            model_name='trafficdata',
            name='timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='vehicle',
            name='traffic_data',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vehicles', to='traffic_app.trafficdata'),
        ),
        migrations.AlterField(
            model_name='vehicle',
            name='trajectory',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='vehicle',
            name='vehicle_type',
            field=models.CharField(choices=[('car', 'Voiture'), ('truck', 'Camion'), ('bus', 'Bus'), ('motorcycle', 'Moto')], default='car', max_length=50),
        ),
    ]
