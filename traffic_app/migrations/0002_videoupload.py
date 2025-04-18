# Generated by Django 5.0 on 2025-01-23 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('traffic_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='VideoUpload',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('video_file', models.FileField(upload_to='uploads/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('processed', models.BooleanField(default=False)),
            ],
        ),
    ]
