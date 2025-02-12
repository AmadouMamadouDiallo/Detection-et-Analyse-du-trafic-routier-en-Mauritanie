from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from .models import TrafficData, Vehicle, VideoUpload
from .detection.video_processing import VideoProcessor, process_video_feed
from django.views.decorators.csrf import csrf_exempt
import json
import folium
from datetime import datetime, timedelta
import os
import logging
from django.conf import settings
import shutil
import time

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'index.html')
def Acceuil(request):
    return render(request, 'Acceuil.html')
@csrf_exempt
def analyze_local_video(request):
    if request.method == 'POST':
        video_path = request.POST.get('video_path')
        logger.info(f"Tentative d'analyse de la vidéo: {video_path}")
        
        if not video_path or not os.path.exists(video_path):
            logger.error(f"Chemin de vidéo invalide ou fichier non trouvé: {video_path}")
            return JsonResponse({
                'error': 'Chemin de vidéo invalide ou fichier non trouvé. '
                        'Assurez-vous que le chemin est correct et que le fichier existe.'
            })
        
        try:
            processor = VideoProcessor()
            logger.info("Début du traitement de la vidéo...")
            
            # Traiter la vidéo
            result = processor.process_video_feed(video_path)
            if not result:
                logger.error("Échec du traitement de la vidéo")
                return JsonResponse({
                    'error': 'Échec du traitement de la vidéo'
                })
            
            # Copier la vidéo traitée dans le dossier media
            media_dir = os.path.join(settings.MEDIA_ROOT, 'processed_videos')
            os.makedirs(media_dir, exist_ok=True)
            output_video = os.path.basename(result['output_video'])
            media_path = os.path.join(media_dir, output_video)
            shutil.copy2(result['output_video'], media_path)
            
            # Calculer les statistiques moyennes
            results = result['results']
            total_vehicles = sum(len(r['detections']) for r in results)
            avg_congestion = sum(r['congestion_level'] for r in results) / len(results)
            
            # Sauvegarder les résultats dans la base de données
            traffic_data = TrafficData.objects.create(
                vehicle_count=total_vehicles,
                congestion_level=avg_congestion,
                latitude=18.0735,  # Coordonnées de Nouakchott
                longitude=-15.9582,
                video_source=video_path
            )
            
            logger.info(f"Analyse terminée avec succès. {total_vehicles} véhicules détectés.")
            
            # Créer l'URL de la vidéo traitée
            video_url = f'/media/processed_videos/{output_video}'
            
            return JsonResponse({
                'success': True,
                'results': {
                    'vehicle_count': total_vehicles,
                    'congestion_level': avg_congestion,
                    'detections': results[0]['detections'] if results else [],
                    'video_url': video_url,
                    'trajectories': result['trajectories']
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de la vidéo: {str(e)}")
            return JsonResponse({
                'error': f'Erreur lors de l\'analyse de la vidéo: {str(e)}'
            })
    
    return render(request, 'analyze_local.html')

import folium
from django.shortcuts import render
from django.db.models import Q
from datetime import datetime
from .models import TrafficData

import folium
from django.shortcuts import render
from django.db.models import Q
from datetime import datetime
from .models import TrafficData

import folium
from django.shortcuts import render
from django.db.models import Q
from datetime import datetime
from .models import TrafficData

# Définition des coordonnées des villes
CITIES = {
    "Nouakchott": [18.0735, -15.9582],
    "Nouadhibou": [20.9333, -17.0333],
    "Kiffa": [16.6228, -11.4058],
    "Kaédi": [16.1500, -13.5000],
    "Sélibaby": [15.1594, -12.1847],
    "Atar": [20.5170, -13.0486],
    "Zouerate": [22.7333, -12.4667],
    "Rosso": [16.5138, -15.8050],
    "Néma": [16.6167, -7.2667],
    "Aleg": [17.0536, -13.9094],
    "Boutilimit": [17.5500, -14.6833],
}

import folium
from django.shortcuts import render
from django.db.models import Q
from datetime import datetime
from .models import TrafficData

def map_view(request):
    available_dates = TrafficData.objects.dates('timestamp', 'day', order='DESC')
    available_locations = TrafficData.objects.values_list('location_name', flat=True).distinct()

    selected_city = request.GET.get('selected_city', 'Nouakchott')
    selected_location = request.GET.get('selected_location', '')
    selected_date = request.GET.get('selected_date', '')

    traffic_filters = Q()

    if selected_city in CITIES:
        traffic_filters &= Q(location_name__icontains=selected_city)

    if selected_location:
        traffic_filters &= Q(location_name__icontains=selected_location)

    if selected_date:
        try:
            selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            traffic_filters &= Q(timestamp__date=selected_date_obj)
        except ValueError:
            selected_date = ''

    traffic_data = TrafficData.objects.filter(traffic_filters).order_by('-timestamp')

    # Centrer la carte sur la première localisation trouvée ou la ville par défaut
    if traffic_data.exists():
        first_data = traffic_data.first()
        map_center = [first_data.latitude, first_data.longitude]
    else:
        map_center = CITIES.get(selected_city, [18.0735, -15.9582])

    traffic_map = folium.Map(location=map_center, zoom_start=13)

    # Ajouter tous les marqueurs
    for data in traffic_data:
        if data.congestion_level >= 0.8:
            color = 'red'
            icon = 'exclamation-triangle'
        elif data.congestion_level >= 0.5:
            color = 'orange'
            icon = 'car'
        else:
            color = 'green'
            icon = 'check-circle'

        popup_info = f'''
        <b>Localisation :</b> {data.location_name} <br>
        <b>Véhicules :</b> {data.vehicle_count} <br>
        <b>Congestion :</b> {data.congestion_level:.1%} <br>
        <b>Heure :</b> {data.timestamp.strftime('%H:%M')} <br>
        '''

        if data.congestion_level >= 0.8:
            popup_info += "<b style='color:red;'>🚨 EMBOUTEILLAGE 🚨</b>"

        folium.Marker(
            location=[data.latitude, data.longitude],
            popup=folium.Popup(popup_info, max_width=300),
            icon=folium.Icon(color=color, icon=icon, prefix='fa'),
            tooltip=data.location_name
        ).add_to(traffic_map)

    context = {
        'map': traffic_map._repr_html_(),  # Assurez-vous que la carte est bien rendue
        'available_dates': available_dates,
        'available_locations': available_locations,
        'selected_date': selected_date,
        'selected_city': selected_city,
        'selected_location': selected_location,
        'cities': CITIES.keys(),
    }
    return render(request, 'map.html', context)







from django.shortcuts import render
from django.db.models import Q
from datetime import datetime
from .models import TrafficData, VideoUpload, Vehicle

from django.shortcuts import render
from django.db.models import Q
from datetime import datetime
from .models import TrafficData, VideoUpload, Vehicle

from django.shortcuts import render
from django.db.models import Q
from datetime import datetime
from .models import TrafficData, VideoUpload, Vehicle

def stats_view(request):
    # Récupérer les dates et localisations uniques pour le menu déroulant
    available_dates = VideoUpload.objects.dates('upload_date', 'day', order='DESC')
    available_locations = VideoUpload.objects.values_list('location', flat=True).distinct()

    # Récupérer les filtres sélectionnés
    selected_date = request.GET.get('selected_date', '')
    selected_location = request.GET.get('selected_location', '')

    filters = Q()

    # Appliquer le filtre sur `VideoUpload`
    if selected_date:
        try:
            selected_date = datetime.strptime(selected_date, "%Y-%m-%d").strftime("%Y-%m-%d")
            filters &= Q(upload_date__date=selected_date)
        except ValueError:
            selected_date = ''

    if selected_location:
        filters &= Q(location=selected_location)

    # Filtrer les vidéos uploadées
    video_uploads = VideoUpload.objects.filter(filters).order_by('-upload_date')

    # Appliquer le même filtre sur `TrafficData`
    traffic_filters = Q()
    if selected_date:
        traffic_filters &= Q(timestamp__date=selected_date)  # Utiliser timestamp car c'est la date des données de trafic
    if selected_location:
        traffic_filters &= Q(location_name=selected_location)  # Utiliser `location_name` au lieu de `location`

    latest_data = TrafficData.objects.filter(traffic_filters).order_by('-timestamp')

    vehicles = Vehicle.objects.all()

    # Statistiques après filtrage
    total_vehicles = sum(data.vehicle_count for data in latest_data)
    total_videos = video_uploads.count()
    avg_congestion = (sum(data.congestion_level for data in latest_data) / len(latest_data)) if latest_data else 0

    # Déterminer l'heure de pointe
    hour_counts = {}
    for data in latest_data:
        hour = data.timestamp.strftime('%H:00')
        hour_counts[hour] = hour_counts.get(hour, 0) + data.vehicle_count
    peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else "N/A"

    # Graphiques
    traffic_labels = [data.timestamp.strftime('%H:%M') for data in latest_data]
    traffic_data = [data.vehicle_count for data in latest_data]

    vehicle_types = ['Voitures', 'Camions', 'Bus', 'Motos']
    vehicle_counts = [
        vehicles.filter(vehicle_type='car').count(),
        vehicles.filter(vehicle_type='truck').count(),
        vehicles.filter(vehicle_type='bus').count(),
        vehicles.filter(vehicle_type='motorcycle').count()
    ]

    # Historique filtré
    analysis_history = [
        {
            'upload_date': upload.upload_date,
            'location': upload.location,
            'vehicle_count': upload.vehicle_count,
            'congestion_level': upload.congestion_level * 100,
            'processing_time': upload.processing_time,
            'status': upload.status
        } for upload in video_uploads
    ]

    context = {
        'total_vehicles': total_vehicles,
        'total_videos': total_videos,
        'peak_hour': peak_hour,
        'avg_congestion': round(avg_congestion * 100, 1),  # Conversion en pourcentage
        'traffic_labels': traffic_labels,
        'traffic_data': traffic_data,
        'vehicle_types': vehicle_types,
        'vehicle_counts': vehicle_counts,
        'analysis_history': analysis_history,
        'available_dates': available_dates,
        'available_locations': available_locations,
        'selected_date': selected_date,
        'selected_location': selected_location
    }

    return render(request, 'stats.html', context)


from django.http import JsonResponse
from django.shortcuts import redirect
from .models import VideoUpload, TrafficData, Vehicle

def clear_history(request):
    if request.method == "POST":
        # Supprimer toutes les entrées de l'historique
        VideoUpload.objects.all().delete()
        TrafficData.objects.all().delete()
        Vehicle.objects.all().delete()
        return JsonResponse({'success': True, 'message': "Historique supprimé avec succès"})
    
    return JsonResponse({'success': False, 'message': "Requête invalide"}, status=400)




@csrf_exempt
def process_video(request):
    if request.method == 'POST' and request.FILES.get('video'):
        video_file = request.FILES['video']
        results = process_video_feed(video_file)
        return JsonResponse(results)
    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_traffic_data(request):
    data = TrafficData.objects.all().order_by('-timestamp')[:100]
    traffic_info = [{
        'timestamp': item.timestamp,
        'vehicle_count': item.vehicle_count,
        'congestion_level': item.congestion_level,
        'latitude': item.latitude,
        'longitude': item.longitude
    } for item in data]
    return JsonResponse({'traffic_data': traffic_info})

@csrf_exempt
def upload_video(request):
    if request.method == 'POST' and request.FILES.get('video'):
        try:
            start_time = time.time()
            video_file = request.FILES['video']
            location = request.POST.get('location', 'Nouakchott, Mauritanie')
            
            # Créer l'entrée VideoUpload
            video_upload = VideoUpload.objects.create(
                video_file=video_file,
                location=location,
                status='processing'
            )
            
            # Obtenir le chemin du fichier uploadé
            video_path = video_upload.video_file.path
            
            # Traiter la vidéo
            processor = VideoProcessor()
            result = processor.process_video_feed(video_path)
            
            if result:
                # Calculer le temps de traitement
                processing_time = time.time() - start_time
                
                # Mettre à jour VideoUpload
                video_upload.processed = True
                video_upload.status = 'completed'
                video_upload.vehicle_count = len(result.get('results', []))
                video_upload.congestion_level = sum(r['congestion_level'] for r in result['results']) / len(result['results'])
                video_upload.processing_time = processing_time
                video_upload.save()
                
                # Créer une entrée TrafficData
                traffic_data = TrafficData.objects.create(
                    vehicle_count=video_upload.vehicle_count,
                    congestion_level=video_upload.congestion_level,
                    latitude=18.0735,  # Coordonnées de Nouakchott
                    longitude=-15.9582,
                    video_source=video_path,
                    location_name=location
                )
                
                # Enregistrer les véhicules détectés
                for detection in result.get('results', []):
                    for vehicle in detection.get('detections', []):
                        Vehicle.objects.create(
                            traffic_data=traffic_data,
                            vehicle_type=vehicle['class'],
                            confidence_score=vehicle['confidence']
                        )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Vidéo traitée avec succès',
                    'results': {
                        'vehicle_count': video_upload.vehicle_count,
                        'congestion_level': video_upload.congestion_level,
                        'processing_time': processing_time,
                        'processed_video_url': video_upload.video_file.url
                    }
                })
            else:
                video_upload.status = 'failed'
                video_upload.error_message = 'Erreur lors du traitement de la vidéo'
                video_upload.save()
                return JsonResponse({
                    'success': False,
                    'error': 'Erreur lors du traitement de la vidéo'
                })
                
        except Exception as e:
            if 'video_upload' in locals():
                video_upload.status = 'failed'
                video_upload.error_message = str(e)
                video_upload.save()
            logger.error(f"Erreur lors du traitement de la vidéo: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f"Erreur: {str(e)}"
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Méthode non autorisée ou fichier manquant'
    })
from django.http import JsonResponse
import random

def process_video(request):
    if request.method == 'POST':
        video_path = request.POST.get('video_path')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        traffic_levels = ['fluide', 'modéré', 'dense']
        traffic_level = random.choice(traffic_levels)

        return JsonResponse({
            'results': {
                'video_url': '/static/videos/processed.mp4',
                'vehicle_count': random.randint(1, 50),
                'congestion_level': random.uniform(0.1, 1.0),
                'latitude': latitude,
                'longitude': longitude,
                'traffic_level': traffic_level
            }
        })

    return JsonResponse({'error': 'Méthode non autorisée'}, status=400)
