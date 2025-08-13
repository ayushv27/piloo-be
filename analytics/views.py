# ------------------------------------------------------------------------
# Copyright (c) 2025 Piloo.ai
#
# Piloo.ai - AI-Powered CCTV Monitoring Platform
# Copyright © 2025 Pyrack Solutions Pvt. Ltd.
# Website: https://pyrack.com/
# All rights reserved. Proprietary software.
# ------------------------------------------------------------------------
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.http import JsonResponse, StreamingHttpResponse
from pathlib import Path

from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from rest_framework.views import APIView
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta, time
from core.models import Client, Camera, Zone, Alert, Employee, Report
from .serializers import *
import time
from core.utils import get_cdn_url
import json
from rest_framework.authtoken.models import Token
import redis
import datetime as dt
from django.utils.timezone import make_aware
from django.http import FileResponse
from .utils import (
    generate_pdf_report,
    send_wa_alert_template_notification,
    send_wa_report_template_notification,
    create_heat_map, 
    create_pie_chart, 
    get_highest_alert,
    get_most_frequent_alert_per_camera, generate_pdf_report_by_date,
    # generate_pdf_report_pdfkit,
)
from django.db.models import Count
from .tasks import send_alert_email
from .report_utils import generate_single_pdf, merge_pdfs

from rest_framework.exceptions import ParseError, ValidationError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.exceptions import APIException
from django.db.models.functions import TruncDate
from rest_framework.generics import ListAPIView
from django.utils.dateparse import parse_date
import os, io
import os
import boto3
import uuid

s3 = boto3.client("s3", aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

# def sse_test(request):
#     def event_stream():
#         while True:
#             yield f"data: {timezone.now().isoformat()}\n\n".encode()
#             time.sleep(2)
#     return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

# def flush_stream(generator):
#     for item in generator:
#         yield ":\n\n"
#         # yield item.encode("utf-8") + b"\n"


# def event_stream(user):
#     previous_data = None
#     count = 0
#     print("previous_data1", previous_data)
#     while True:
#         # now = timezone.now().isoformat()
#         # msg = f"data: {now}\n\n"
#         # print("Sending:", msg)
#         # yield msg
#         # count += 1
#         # time.sleep(2)
#         stats = get_dashboard_stats_sync(user)
#         if stats != previous_data:
#             message = f"data: {json.dumps(stats)}\n\n"
#             print('message', message)
#             yield message
#             sys.stdout.flush()  # ensures print shows up, not the fix for curl
#             previous_data = stats
#             print("previous_data2", previous_data)
#         else:
#             print("No change in stats")
#         time.sleep(5)


# def sse_message_generator(user):
#     previous_data = None
#     while True:
#         stats = get_dashboard_stats_sync(user)
#         if stats != previous_data:
#             message = f"data: {json.dumps(stats)}\n\n"
#             yield message
#             previous_data = stats
#         else:
#             yield "no change in data\n\n"  # heartbeat
#         time.sleep(5)


# def get_dashboard_stats_sync(user):
#     print('received request')
#     today = timezone.now().date()
#     print("today's timestamp::", today)

#     active_cameras = Camera.objects.filter(owner=user.company, status='active').count()
#     today_incidents = Alert.objects.filter(camera__owner=user.company, timestamp__date=today).count()
#     current_alerts = Alert.objects.filter(camera__owner=user.company, status='active').count()
#     recent_alerts = list(
#         Alert.objects.filter(owner=user.company)
#         .select_related("camera")
#         .order_by("-timestamp")[:5]
#         .values(
#             "timestamp", "camera__name", "thumbnail_url", "camera__location", "type"
#         )
#     )
#     employees_today = Employee.objects.filter(owner=user.company, date=today)
#     print('active_cameras', active_cameras)
#     print('today_incidents', today_incidents)
#     print('current_alerts', current_alerts)
#     employee_stats = {
#         'present': employees_today.filter(status='present').count(),
#         'absent': employees_today.filter(status='absent').count(),
#         'late': employees_today.filter(status='late').count(),
#         'avgDuration': '8h 30m'  # Placeholder
#     }

#     total_zones = Zone.objects.filter(owner=user.company).count()
#     covered_zones = Camera.objects.filter(owner=user.company, status='active').values('assigned_zone').distinct().count()
#     zone_coverage = f"{covered_zones}/{total_zones} zones"
#     print('total_zones', total_zones)
#     print('covered_zones', covered_zones)
#     print('zone_coverage', zone_coverage)

#     return {
#         'activeCameras': active_cameras,
#         'todayIncidents': today_incidents,
#         'currentAlerts': current_alerts,
#         'zoneCoverage': zone_coverage,
#         'recentAlerts': recent_alerts,
#         # 'employeeStats': employee_stats
#     }


# def dashboard_stats_sse(request):
#     token = request.GET.get('token')
#     if not token:
#         return JsonResponse({'error': 'Token required'}, status=401)
#     try:
#         user = Token.objects.get(key=token).user
#     except Token.DoesNotExist:
#         return JsonResponse({'error': 'Invalid token'}, status=401)

#     def threaded_stream():
#         yield from sse_message_generator(user)

#     response = StreamingHttpResponse(threaded_stream(), content_type='text/event-stream')
#     response['Cache-Control'] = 'no-cache'
#     response['X-Accel-Buffering'] = 'no'
#     # response['Connection'] = 'keep-alive'
#     return response


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def dashboard_stats_sse(request):
#     token = request.GET.get('token')
#     if not token:
#         return Response({'error': 'Token required'}, status=401)
#     try:
#         user = Token.objects.get(key=token).user
#     except Token.DoesNotExist:
#         return Response({'error': 'Invalid token'}, status=401)
#     print('user::', user)
#     response = StreamingHttpResponse(event_stream(user), content_type='text/event-stream')
#     print("response", response)
#     response['Cache-Control'] = 'no-cache'
#     # response['Cache-Control'] = 'no-cache'
#     response['Content-Type'] = 'text/event-stream'
#     response['X-Accel-Buffering'] = 'no'  # for nginx or proxies
#     response['Connection'] = 'keep-alive'
#     return response


# Dashboard Statistics View
@api_view(["GET"])
# @permission_classes([IsAuthenticated])
def dashboard_stats(request):
    user = request.user
    today = timezone.now().date()

    # Calculate statistics
    active_cameras = Camera.objects.filter(owner=user.company, status="active").count()
    today_incidents = Alert.objects.filter(
        camera__owner=user.company, timestamp__date=today
    ).count()
    current_alerts = Alert.objects.filter(
        camera__owner=user.company, status="active"
    ).count()

    # Employee stats
    employees_today = Employee.objects.filter(company=user.company, date=today)
    employee_stats = {
        "present": employees_today.filter(status="present").count(),
        "absent": employees_today.filter(status="absent").count(),
        "late": employees_today.filter(status="late").count(),
        "avgDuration": "8h 30m",  # This would be calculated based on check-in/out times
    }

    # Zone coverage calculation
    total_zones = Zone.objects.filter(owner=user.company).count()
    covered_zones = (
        Camera.objects.filter(owner=user.company, status="active")
        .values("assigned_zone")
        .distinct()
        .count()
    )

    zone_coverage = f"{covered_zones}/{total_zones} zones"

    stats = {
        "activeCameras": active_cameras,
        "todayIncidents": today_incidents,
        "currentAlerts": current_alerts,
        "zoneCoverage": zone_coverage,
        "employeeStats": employee_stats,
    }

    serializer = StatsSerializer(stats)
    return Response(serializer.data)


def sse_camera_status_updates(request):
    def event_stream():
        pubsub = redis.StrictRedis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0
        ).pubsub()
        pubsub.subscribe("camera_status_updates")
        for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                yield f"data: {json.dumps(data)}\n\n"
            time.sleep(0.1)

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")


# Analytics Views
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def analytics_overview(request):
    user = request.user
    today = timezone.now().date()
    from_date = request.query_params.get("fromDate")
    to_date = request.query_params.get("toDate")
    alerts = Alert.objects.filter(camera__owner=user.company)
    if from_date:
        try:
            from_dt = make_aware(datetime.strptime(f"{from_date}", "%Y-%m-%d"))
            alerts = alerts.filter(timestamp__gte=from_dt)
        except ValueError:
            raise ParseError(
                "Invalid 'fromDate' or 'fromTime' format. Expected format: YYYY-MM-DD HH:MM:SS"
            )
    if to_date:
        try:
            from_dt = make_aware(datetime.strptime(f"{to_date}", "%Y-%m-%d"))
            alerts = alerts.filter(timestamp__gte=from_dt)
        except ValueError:
            raise ParseError(
                "Invalid 'fromDate' or 'fromTime' format. Expected format: YYYY-MM-DD HH:MM:SS"
            )
    analytics = {
        "totalIncidents": alerts.count(),
        "todayIncidents": alerts.filter(timestamp__date=today).count(),
        "activeCameras": Camera.objects.filter(
            owner=user.company, status="active"
        ).count(),
        "criticalAlerts": alerts.filter(
            usecase__severity="critical", status="active"
        ).count(),
        "resolvedIncidents": alerts.filter(status="resolved").count(),
        "avgResponseTime": 15,  # This would be calculated from alert resolution times
    }

    serializer = AnalyticsSerializer(analytics)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def incident_trends(request):
    user = request.user
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    # This would typically involve complex aggregation queries
    # For now, returning sample data structure
    trends = []
    current_date = start_date

    while current_date <= end_date:
        daily_alerts = Alert.objects.filter(
            camera__owner=user.company, timestamp__date=current_date
        )

        trend_data = {
            "date": current_date.strftime("%Y-%m-%d"),
            "incidents": daily_alerts.count(),
            "resolved": daily_alerts.filter(status="resolved").count(),
            "critical": daily_alerts.filter(usecase__severity="critical").count(),
            "high": daily_alerts.filter(usecase__severity="high").count(),
            "medium": daily_alerts.filter(usecase__severity="medium").count(),
            "low": daily_alerts.filter(usecase__severity="low").count(),
        }
        trends.append(trend_data)
        current_date += timedelta(days=1)

    serializer = IncidentTrendSerializer(trends, many=True)
    return Response(serializer.data)

"""
@date: 2025-08-04
@change: Made changes to the alert_distribution view to include filtering by date, zone, and camera.
"""
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def alert_distribution(request):
    user = request.user
    start_date_str = request.query_params.get('start_date', None)
    end_date_str = request.query_params.get('end_date', None)
    zone = request.query_params.get('zone_id', None)
    camera = request.query_params.get('camera_id', None)
    client_id = request.user.company.id
    print("client_id", client_id)
    
    alert_counts = (
        Alert.objects.filter(camera__owner=client_id)
        .values("usecase__usecase__type", "label")
        .annotate(count=Count("label"))
    )
    # try:
    #     if start_date_str and end_date_str:
    #         start_date = make_aware(datetime.fromisoformat(start_date_str))
    #         end_date = make_aware(datetime.fromisoformat(end_date_str))

    #         if start_date.date() == end_date.date():
    #             end_date = end_date + timedelta(days=1) 
    #     else:
    #         start_date = end_date = None
    # except ValueError:
    #     return Response({'error': 'Invalid date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).'}, status=400)
    

# filter options on dashboard
    # if start_date and end_date:
    #     alert_counts = alert_counts.filter(timestamp__range=(start_date, end_date))
    
    start = end = None
    if start_date_str:
        sd = parse_date(start_date_str)
        if not sd:
            raise ValidationError({"start_date": "Invalid format. Use YYYY-MM-DD."})        
        start = timezone.make_aware(dt.datetime.combine(sd, dt.time.min))

    if end_date_str:
        ed = parse_date(end_date_str)
        if not ed:
            raise ValidationError({"end_date": "Invalid format. Use YYYY-MM-DD."})       
        end = timezone.make_aware(dt.datetime.combine(ed + dt.timedelta(days=1), dt.time.min))

    # apply to queryset
    if start and end:
        alert_counts = alert_counts.filter(timestamp__gte=start, timestamp__lt=end)
    elif start:
        alert_counts = alert_counts.filter(timestamp__gte=start)
    elif end:
        alert_counts = alert_counts.filter(timestamp__lt=end)
    

    # if zone:       
    #     alert_counts = alert_counts.filter(camera__assigned_zone=zone)
    # if camera:
    #     alert_counts = alert_counts.filter(camera=camera)

    if zone:
        try:
            zone_uuid = uuid.UUID(zone)
        except ValueError:
            raise ValidationError({"zone_id": "Invalid UUID format."})
        alert_counts = alert_counts.filter(camera__assigned_zone=zone_uuid)

    if camera:
        try:
            camera_uuid = uuid.UUID(camera)
        except ValueError:
            raise ValidationError({"camera_id": "Invalid UUID format."})
        alert_counts = alert_counts.filter(camera=camera_uuid)           
        
        
    total_alerts = sum(item["count"] for item in alert_counts)

    distribution = []
    for item in alert_counts:
        distribution.append(
            {
                "name": item["usecase__usecase__type"],
                "value": item["count"],
                "percentage": (
                    round((item["count"] / total_alerts) * 100, 2)
                    if total_alerts > 0
                    else 0
                ),
            }
        )

    serializer = AlertDistributionSerializer(distribution, many=True)
    return Response(serializer.data)


    # start_date_str = request.query_params.get('start_date', None)
    # end_date_str = request.query_params.get('end_date', None)
    # zone = request.query_params.get('zone', None)
    # camera = request.query_params.get('camera', None)
    # client_id = request.user.company.id
    # alert_counts = (
    #     Alert.objects.filter(camera__owner=user.company)
    #     .values("label", "camera__assigned_zone__name")
    #     .annotate(count=Count("id"))
    # )

    # total_alerts = sum(item["count"] for item in alert_counts)

    # # Group distribution by zone
    # zone_distribution = defaultdict(list)

    # for item in alert_counts:
    #     zone = item["camera__assigned_zone__name"] or "Unassigned"
    #     label = item["label"] or "Unknown Alert"
    #     count = item["count"]

    #     zone_distribution[zone].append({
    #         "name": label,
    #         "value": count,
    #         "percentage": round((count / total_alerts) * 100, 2) if total_alerts else 0
    #     })

    # result = [
    #     {
    #         "zone": zone,
    #         "alerts": alerts
    #     }
    #     for zone, alerts in zone_distribution.items()
    # ]

    # return Response(result)


# Additional Analytics Views
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def occupancy_analytics(request):
    user = request.user
    zones = Zone.objects.filter(owner=user.company)

    occupancy_data = []
    for zone in zones:
        # This would typically involve people counting from camera feeds
        # For now, using mock data
        occupancy_data.append(
            {
                "zone": zone.name,
                "occupancy": 8,  # Mock current occupancy
                "capacity": 20,  # Mock zone capacity
                "percentage": 40.0,  # Mock percentage
            }
        )

    serializer = OccupancySerializer(occupancy_data, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def camera_performance(request):
    user = request.user
    cameras = Camera.objects.filter(owner=user.company)

    performance_data = []
    for camera in cameras:
        # Calculate performance metrics
        total_alerts = Alert.objects.filter(camera=camera).count()

        performance_data.append(
            {
                "id": camera.id,
                "name": camera.name,
                "uptime": 99.5,  # Mock uptime percentage
                "alerts": total_alerts,
                "lastMaintenance": timezone.now() - timedelta(days=30),  # Mock
                "status": camera.status,
            }
        )

    serializer = CameraPerformanceSerializer(performance_data, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def activity_heatmap(request):
    
    start_date_str = request.query_params.get('start_date', None)
    end_date_str = request.query_params.get('end_date', None)
    zone = request.query_params.get('zone_id', None)
    camera = request.query_params.get('camera_id', None)
    client_id = request.user.company.id

    # try:
    #     if start_date_str and end_date_str:
    #         start_date = make_aware(datetime.fromisoformat(start_date_str))
    #         end_date = make_aware(datetime.fromisoformat(end_date_str))
    #     else:
    #         start_date = end_date = None
    # except ValueError:
    #     return Response({'error': 'Invalid date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).'}, status=400)

    # Now filter
    alerts = Alert.objects.filter(owner_id=client_id)

    # if start_date and end_date:
    #     alerts = alerts.filter(timestamp__range=(start_date, end_date))

    start = end = None
    if start_date_str:
        sd = parse_date(start_date_str)
        if not sd:
            raise ValidationError({"start_date": "Invalid format. Use YYYY-MM-DD."})        
        start = timezone.make_aware(dt.datetime.combine(sd, dt.time.min))

    if end_date_str:
        ed = parse_date(end_date_str)
        if not ed:
            raise ValidationError({"end_date": "Invalid format. Use YYYY-MM-DD."})       
        end = timezone.make_aware(dt.datetime.combine(ed + dt.timedelta(days=1), dt.time.min))

    # apply to queryset
    if start and end:
        alerts = alerts.filter(timestamp__gte=start, timestamp__lt=end)
    elif start:
        alerts = alerts.filter(timestamp__gte=start)
    elif end:
        alerts = alerts.filter(timestamp__lt=end)

    # if zone:
    #     alerts = alerts.filter(camera__assigned_zone=zone)
    # if camera:
    #     alerts = alerts.filter(camera=camera)

    if zone:
        try:
            zone_uuid = uuid.UUID(zone)
        except ValueError:
            raise ValidationError({"zone_id": "Invalid UUID format."})
        alerts = alerts.filter(camera__assigned_zone=zone_uuid)

    if camera:
        try:
            camera_uuid = uuid.UUID(camera)
        except ValueError:
            raise ValidationError({"camera_id": "Invalid UUID format."})
        alerts = alerts.filter(camera=camera_uuid)

    camera_data_qs = alerts.values("camera__name", "label").annotate(count=Count("id"))

    # Convert to structure suitable for plotting
    camera_events_dict = {}
    for entry in camera_data_qs:
        camera_name = entry["camera__name"]
        label = entry["label"]
        count = entry["count"]

        if camera_name not in camera_events_dict:
            camera_events_dict[camera_name] = {}
        camera_events_dict[camera_name][label] = count

    # Format like original structure
    heatmap_data = [{cam: data} for cam, data in camera_events_dict.items()]

    # serializer = ActivityHeatmapSerializer(heatmap_data, many=True)
    return Response(heatmap_data)


class GenerateReportView(APIView):
    def get(self, request, *args, **kwargs):
        client_id = request.query_params.get('client')
        try:
            client = Client.objects.get(id=client_id)
            alerts = Alert.objects.filter(owner_id=client_id)
            print(alerts)
            pie_data_qs = alerts.values("label").annotate(count=Count("id"))
            pie_data = {entry["label"]: entry["count"] for entry in pie_data_qs}
 
            print('pie_data', pie_data)
            
            pie_path  = create_pie_chart(pie_data)
            
            camera_data_qs = alerts.values("camera__name", "label").annotate(count=Count("id"))


            # Convert to structure suitable for plotting
            camera_events_dict = {}
            for entry in camera_data_qs:
                camera_name = entry["camera__name"]
                label = entry["label"]
                count = entry["count"]

                if camera_name not in camera_events_dict:
                    camera_events_dict[camera_name] = {}
                camera_events_dict[camera_name][label] = count


            # Format like original structure
            camera_events = [{cam: data} for cam, data in camera_events_dict.items()]

            print('camera_events', camera_events)
            
            stack_path = create_heat_map(camera_events)
            max_camera, max_alert_type = get_highest_alert(camera_events)
            result = get_most_frequent_alert_per_camera(camera_events)
            print('result', result)
            camera_alerts = (
            Alert.objects.values('camera__id', 'camera__name', 'camera__location', 'label', 'usecase__usecase__type')
            .annotate(alert_count=Count('id'))
            .order_by('camera__id', '-alert_count')
            )


            # Organize by camera, keeping the top alert type per camera
            seen = set()
            alert_cards = []


            for alert in pie_data_qs:
                latest_alert = Alert.objects.filter(label=alert['label']).order_by('-timestamp').select_related('camera').first()


                if latest_alert:
                    alert_cards.append({
                        "image_url": latest_alert.frame_url,
                        "alert_type": latest_alert.label,
                        "camera_name": latest_alert.camera.name,
                        "location": latest_alert.camera.location,
                        "timestamp": latest_alert.timestamp,
                    })
            context = {
                "client_name": client.name,
                "report_period": "June 2025 - July 2025",
                "plan": client.subscription_plan.name,
                "total_events": client.client_alerts.count(),
                "max_camera": max_camera,
                "max_alert_type": max_alert_type,
                "most_frequent_alerts": result,
                "alert_cards": alert_cards,
                "active_cameras": client.cameras.count(),
                "pie_chart_path": os.path.join(settings.MEDIA_URL, pie_path),
                "stack_path": os.path.join(settings.MEDIA_URL, stack_path),
            }
            print("context", context)
            
            
            # List of HTML files to convert
            base_url = Path(__file__).resolve().parent.parent
            html_files = [
                os.path.join(base_url, "templates/report_page1.html"),
                os.path.join(base_url, "templates/report_page2.html"),
                os.path.join(base_url, "templates/report_page3.html"),
                # os.path.join(base_url, "templates/index3.html"),
                # os.path.join(base_url, "templates/index4.html"),
            ]


            # Check file existence
            missing_files = [f for f in html_files if not os.path.exists(f)]
            if missing_files:
                raise APIException(f"Missing HTML files: {', '.join(missing_files)}")


            # Convert each HTML to PDF bytes
            pdf_bytes_list = []
            for html_file in html_files:
                try:
                    pdf_bytes = generate_single_pdf(html_file, base_url, context)
                    pdf_bytes_list.append(pdf_bytes)
                except Exception as e:
                    raise APIException(f"Failed to generate PDF for {html_file}: {str(e)}")


            # Merge PDFs
            try:

                # Generate a safe filename with no colons or spaces
                timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                filename = f"Report_{client_id}_{timestamp}.pdf"
                s3_path = f"reports/{filename}"
                local_path = os.path.join('media', filename)  
                
                # Step 1: Merge and save locally
                merge_pdfs(pdf_bytes_list, local_path)
                s3.upload_file(
                    Filename=local_path,
                    Bucket=settings.S3_BUCKET,  # Make sure this is set earlier
                    Key=s3_path,
                    ExtraArgs={
                        "ContentType": "application/pdf",  # or "image/png" or "image/jpeg" etc.
                        "CacheControl": "no-cache"
                    }
                )

                report = Report.objects.create(client_id=client_id, report=s3_path)


                # Step 3: Clean up local file
                if os.path.exists(local_path):
                    os.remove(local_path)


                # Step 4: Return the S3/CDN URL
                report_url = get_cdn_url(report.report.name)
                print('Uploaded report to:', report_url)
            except Exception as e:
                raise APIException(f"Failed to merge PDFs: {str(e)}")
            return Response(report_url)

        except Exception as e:
            raise APIException(f"PDF generation failed: {str(e)}")
        
        


@api_view(["POST"])
def send_notification(request):
    data = request.data

    camera_id = data.get("camera_id")
    clip_url = data.get("chunk_url")
    label = data.get("label")
    timestamp = data.get("timestamp")
    thumbnail_url = data.get("thumbnail_url")
    date_part, time_part = timestamp.split("T")
    time_fixed = time_part.replace("-", ":", 2).replace("+00-00", "+00:00")
    ts = f"{date_part}T{time_fixed}"

    tp = datetime.fromisoformat(ts)
    print(tp.strftime("%-d %b %y"))
    alert_date = tp.strftime("%-d %b %y")
    alert_time = tp.strftime("%H:%M")
    if not all([camera_id, clip_url, label, timestamp]):
        return Response(
            {"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        camera = Camera.objects.select_related("owner", "assigned_zone").get(
            id=camera_id
        )
    except ObjectDoesNotExist:
        return Response({"error": "Camera not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        camera_name = camera.name
        client_id = camera.owner.id
        zone_name = camera.assigned_zone.name
        client_name = camera.owner.name
        report_url = os.path.join(settings.CDN_DOMAIN, 'Report.pdf')
        # Sandbox number; replace with real number in prod
        to_numbers = Client.objects.filter(id=client_id).values_list(
            "phone", flat=True
        )
        # to_numbers = ['+918976179141']
        # to_numbers = list[camera.owner.phone]
        print(to_numbers)
        #
        for to_number in to_numbers:
            # Send alert notification
            send_wa_alert_template_notification(
                to_number,
                client_name,
                clip_url,
                thumbnail_url,
                label,
                alert_date,
                alert_time,
                zone_name,
                camera_name,
            )

            # Send report notification
            send_wa_report_template_notification(to_number, client_name, report_url)


        return Response(
            {"message": "Notification sent successfully"}, status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(["POST"])
def send_criticle_notification(request):
    data = request.data

    camera_id = data.get("camera_id")
    clip_url = data.get("chunk_url")
    label = data.get("label")
    timestamp = data.get("timestamp")
    thumbnail_url = data.get("thumbnail_url")
    date_part, time_part = timestamp.split("T")
    time_fixed = time_part.replace("-", ":", 2).replace("+00-00", "+00:00")
    ts = f"{date_part}T{time_fixed}"

    tp = datetime.fromisoformat(ts)
    print(tp.strftime("%-d %b %y"))
    alert_date = tp.strftime("%-d %b %y")
    alert_time = tp.strftime("%H:%M")
    if not all([camera_id, clip_url, label, timestamp]):
        return Response(
            {"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        camera = Camera.objects.select_related("owner", "assigned_zone").get(
            id=camera_id
        )
    except ObjectDoesNotExist:
        return Response({"error": "Camera not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        camera_name = camera.name
        to_email = camera.owner.email
        client_id = camera.owner.id
        zone_name = camera.assigned_zone.name
        client_name = camera.owner.name
        severity = 'medium"'
        # report_url = f"{settings.CDN_DOMAIN}/Report.pdf"
        # print('trying to generate pdf')
        # report_url = generate_pdf_report(client_id)
        # Sandbox number; replace with real number in prod
        to_numbers = Client.objects.filter(id=client_id).values_list(
            "phone", flat=True
        )
        # to_numbers = ['+919890880009']
        # print(to_numbers)
        # to_numbers = camera.owner.phone
        #
        for to_number in to_numbers:
            # Send alert notification
            send_wa_alert_template_notification(
                to_number,
                client_name,
                clip_url,
                thumbnail_url,
                label,
                alert_date,
                alert_time,
                zone_name,
                camera_name,
            )

            # Send report notification
            # send_wa_report_template_notification(to_number, client_name, report_url)
            send_alert_email(
            to_email,
            client_name,
            severity,
            label,
            alert_date,
            alert_time,
            zone_name,
            camera_name,
            clip_url,
            thumbnail_url,
        )
        return Response(
            {"message": "Notification sent successfully"}, status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# testing purpose
from .utils import generate_pdf_report_alerts
class GeneratePDFReportAPI(APIView):
    def get(self, request, client_id):
        try:
            #send_wa_report_template_notification("+919890880009","Hrishabh", "https://image.piloo.ai/Report.pdf")
            # report_url = generate_pdf_report_alerts(client_id)
            report_url = generate_pdf_report(client_id)
            if report_url:
                return Response({"status": "success", "report_url": report_url}, status=status.HTTP_200_OK)
            else:
                return Response({"status": "failed", "message": "Report generation failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print("Error generating report:", str(e))
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


"""
@author: Mandar More
@date: 2025-07-30
@description: View to get event count per day for a client.

"""
class ClientEventCountPerDayView(ListAPIView):
    serializer_class = EventCountPerDaySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  

    def get_queryset(self):
        client = self.request.user      

        queryset = Alert.objects.filter(owner=client.company)  

        # Filters for serach
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        zone_id = self.request.query_params.get('zone_id')
        camera_id = self.request.query_params.get('camera_id')

        if start_date and end_date:
            queryset = queryset.filter(created_at__date__range=[start_date, end_date])
        elif start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        elif end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)

        if zone_id:
            try:
                zone_uuid = uuid.UUID(zone_id)
            except ValueError:
                raise ValidationError({"zone_id": "Invalid UUID format."})
            queryset = queryset.filter(camera__assigned_zone_id=zone_uuid)

        if camera_id:
            try:
                camera_uuid = uuid.UUID(camera_id)
            except ValueError:
                raise ValidationError({"camera_id": "Invalid UUID format."})
            queryset = queryset.filter(camera_id=camera_uuid)

        return (
            queryset.annotate(date=TruncDate("created_at"))            
            .values("date", "usecase__usecase__name")
            .annotate(count=Count("id"))
            .order_by("-date")
        )
    
    def get_serializer_context(self):
        return super().get_serializer_context()

    def get_serializer(self, *args, **kwargs):
        """
        Overriding to handle serialized dicts from values().
        """
        data = self.get_queryset()
       
        transformed_data = [
            {
                "date": item["date"],
                'day': item["date"].strftime("%A"),
                "event_name": item["usecase__usecase__name"],
                "count": item["count"]
            }
            for item in data
        ]
        return self.serializer_class(transformed_data, many=True, context=self.get_serializer_context())


"""
@author: Mandar More
@date: 2025-07-31
@description: View to get day-wise alert count for a client.
@date: 2025-08-04
@change: Updated date filtering logic.

"""
class DayWiseAlertCountView(ListAPIView):
    serializer_class = DayWiseAlertCountSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None 

    def get_queryset(self):
        
        client = self.request.user 

        if not hasattr(client, 'company'):
            return Alert.objects.none()     

        queryset = Alert.objects.filter(owner=client.company)  

        # Filters for serach
        start_date_raw  = self.request.query_params.get('start_date')
        end_date_raw  = self.request.query_params.get('end_date')
        zone_id = self.request.query_params.get('zone_id')
        camera_id = self.request.query_params.get('camera_id')        

        start_dt = end_dt = None

        if start_date_raw:
            sd = parse_date(start_date_raw)            
            if not sd:
                return Response({"error": "Invalid start_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
            naive_start = dt.datetime.combine(sd, dt.time.min)          
            start_dt = timezone.make_aware(naive_start)            

        if end_date_raw:
            ed = parse_date(end_date_raw)            
            if not ed:
                return Response({"error": "Invalid end_date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
            naive_end = dt.datetime.combine(ed, dt.time.max)
            end_dt = timezone.make_aware(naive_end)
        
        if start_dt and end_dt:
            queryset = queryset.filter(created_at__range=(start_dt, end_dt))
        elif start_dt:
            queryset = queryset.filter(created_at__gte=start_dt)
        elif end_dt:
            queryset = queryset.filter(created_at__lte=end_dt)

        if zone_id:
            try:
                zone_uuid = uuid.UUID(zone_id)
            except ValueError:
                raise ValidationError({"zone_id": "Invalid UUID format."})
            queryset = queryset.filter(camera__assigned_zone_id=zone_uuid)

        if camera_id:
            try:
                camera_uuid = uuid.UUID(camera_id)
            except ValueError:
                raise ValidationError({"camera_id": "Invalid UUID format."})
            queryset = queryset.filter(camera_id=camera_uuid)
        
        return (
                queryset
                .distinct()
                .annotate(date=TruncDate("created_at"))
                .values("date")
                .annotate(alert_count=Count("id"))
                .order_by("-date")
            )
    
"""
@author: Neha Pawar
"""
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_report(request):
        try:
            client = request.user
            date = request.query_params.get('date')
            print("client company :", client.company_id)
            print("date :", date)
            if  not date:
                return Response({"status": "error", "message": "Date is required"}, status=status.HTTP_400_BAD_REQUEST)
            report_url = generate_pdf_report_by_date(client.company_id, date)
            print("report_url :", report_url)
            if report_url:
                return Response({"status": "success", "report_url": report_url}, status=status.HTTP_200_OK)
            else:
                return Response({"status": "failed", "message": "Report generation failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print("Error generating report:", str(e))
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)    
        


class SendTestAlertView(APIView):
    def get(self, request):
        try:
            send_alert_email(
                to_email="neha.pawar@pyrack.com",
                client_name="Hrishabh",
                severity="critical",
                label="Intrusion Detected",
                alert_date="30 Jul 2025",
                alert_time="12:00",
                zone_name="Main Gate",
                camera_name="Camera 1",
                clip_url="https://image.piloo.ai/streams/hls/89e74bf6-76e9-4294-82ac-55c8d257f708/89e74bf6-76e9-4294-82ac-55c8d257f708_2025-07-30T16-35-59-617179-05-30.m3u8",
                thumbnail_url="https://image.piloo.ai/streams/annotated/89e74bf6-76e9-4294-82ac-55c8d257f708/89e74bf6-76e9-4294-82ac-55c8d257f708_2025-07-30T16-36-03-535656-05-30.jpg"
            )
            return Response({"message": "Test alert email sent successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)