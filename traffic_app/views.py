from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from .models import TrafficData, Vehicle
from .detection.video_processing import VideoProcessor, process_video_feed
from django.views.decorators.csrf import csrf_exempt
import json
import folium
from datetime import datetime, timedelta
import os
import logging
from django.conf import settings
import shutil

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'base.html')

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
                latitude=48.8566,  # Coordonnées par défaut (Paris)
                longitude=2.3522,
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
    # Créer une carte centrée sur Paris
    m = folium.Map(location=[48.8566, 2.3522], zoom_start=13)
    
    # Récupérer les données de trafic
    time_range = request.GET.get('time_range', '24')
    time_threshold = datetime.now() - timedelta(hours=int(time_range))
    traffic_data = TrafficData.objects.filter(timestamp__gte=time_threshold)
    
    # Ajouter les marqueurs à la carte
    for data in traffic_data:
        color = 'green'
        if data.congestion_level > 0.7:
            color = 'red'
        elif data.congestion_level > 0.4:
            color = 'orange'
            
        folium.CircleMarker(
            location=[data.latitude, data.longitude],
            radius=10,
            popup=f'Congestion: {data.congestion_level:.2f}<br>Véhicules: {data.vehicle_count}',
            color=color,
            fill=True,
            fill_color=color
        ).add_to(m)
    
    # Convertir la carte en HTML
    map_html = m._repr_html_()
    
    return render(request, 'map_view.html', {
        'map_html': map_html,
        'time_range': time_range
    })

def stats_view(request):
    latest_data = TrafficData.objects.all().order_by('-timestamp')[:24]
    return render(request, 'stats.html', {'latest_data': latest_data})

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
