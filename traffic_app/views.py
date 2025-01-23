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

def map_view(request):
    # Coordonnées de Nouakchott
    nouakchott_map = folium.Map(
        location=[18.0735, -15.9582],  # Coordonnées de Nouakchott
        zoom_start=13
    )
    
    # Ajouter un marqueur pour le centre-ville
    folium.Marker(
        [18.0735, -15.9582],
        popup='Centre-ville de Nouakchott',
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(nouakchott_map)
    
    # Récupérer les données de trafic
    traffic_data = TrafficData.objects.all()
    
    # Ajouter des marqueurs pour chaque point de données
    for data in traffic_data:
        color = 'green' if data.congestion_level < 0.3 else 'orange' if data.congestion_level < 0.7 else 'red'
        folium.CircleMarker(
            location=[data.latitude, data.longitude],
            radius=10,
            popup=f'Véhicules: {data.vehicle_count}<br>Congestion: {data.congestion_level:.1%}',
            color=color,
            fill=True
        ).add_to(nouakchott_map)
    
    context = {
        'map': nouakchott_map._repr_html_(),
        'city': 'Nouakchott'
    }
    return render(request, 'map.html', context)

def stats_view(request):
    # Récupérer les données pour le dashboard
    latest_data = TrafficData.objects.all().order_by('-timestamp')[:24]
    video_uploads = VideoUpload.objects.all().order_by('-upload_date')
    vehicles = Vehicle.objects.all()

    # Statistiques générales
    total_vehicles = sum(data.vehicle_count for data in latest_data)
    total_videos = video_uploads.count()
    avg_congestion = sum(data.congestion_level for data in latest_data) / len(latest_data) if latest_data else 0
    
    # Déterminer l'heure de pointe (heure avec le plus de véhicules)
    hour_counts = {}
    for data in latest_data:
        hour = data.timestamp.strftime('%H:00')
        hour_counts[hour] = hour_counts.get(hour, 0) + data.vehicle_count
    peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else "N/A"

    # Données pour le graphique d'évolution du trafic
    traffic_labels = [data.timestamp.strftime('%H:%M') for data in latest_data]
    traffic_data = [data.vehicle_count for data in latest_data]

    # Données pour le graphique de distribution des véhicules
    vehicle_types = ['Voitures', 'Camions', 'Bus', 'Motos']
    vehicle_counts = [
        vehicles.filter(vehicle_type='car').count(),
        vehicles.filter(vehicle_type='truck').count(),
        vehicles.filter(vehicle_type='bus').count(),
        vehicles.filter(vehicle_type='motorcycle').count()
    ]

    # Historique des analyses
    analysis_history = []
    for upload in video_uploads:
        analysis = {
            'upload_date': upload.upload_date,
            'location': upload.location,
            'vehicle_count': upload.vehicle_count,
            'congestion_level': upload.congestion_level * 100,
            'processing_time': upload.processing_time,
            'status': upload.status
        }
        analysis_history.append(analysis)

    context = {
        'total_vehicles': total_vehicles,
        'total_videos': total_videos,
        'peak_hour': peak_hour,
        'avg_congestion': round(avg_congestion * 100, 1),
        'traffic_labels': traffic_labels,
        'traffic_data': traffic_data,
        'vehicle_types': vehicle_types,
        'vehicle_counts': vehicle_counts,
        'analysis_history': analysis_history
    }

    return render(request, 'stats.html', context)

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
