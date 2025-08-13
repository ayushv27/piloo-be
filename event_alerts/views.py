from collections import defaultdict
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from qdrant_client import QdrantClient
from datetime import datetime
import pytz
from datetime import datetime, timedelta
from dateutil.parser import isoparse
from django.utils.timezone import get_current_timezone
from django.db import transaction

from core.models import Alert, Camera, Client, ClientUseCase, AlertTypeMaster

from rest_framework import generics
from rest_framework.exceptions import NotFound

from .serializers import AlertTypeMasterSerializer
from rest_framework.permissions import IsAuthenticated


class QdrantTodayDataView(APIView):
    def get(self, request):
        try:
            # Connect to Qdrant
            client = QdrantClient(host="13.127.210.74", port=6333)

            # Get current time in IST
            ist = pytz.timezone("Asia/Kolkata")
            now = datetime.now(ist)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            now_time = now.isoformat()

            print("📅 Using timestamp range:")
            print("  ➤ Start:", today_start)
            print("  ➤ End  :", now_time)

            # Scroll without filter for now (or enable filter if needed)
            scroll_result = client.scroll(
                collection_name="client_f2f190af-fb87-4c38-b974-91af6db49786_domain_general_surveillance",
                scroll_filter=None,  # You can add time filter here if Qdrant supports it
               
                # scroll_filter={
                #     "must": [
                #         {
                #             "key": "timestamp",
                #             "range": {
                #                 "gte": today_start,
                #                 "lte": now_time
                #             }
                #         }
                #     ]
                # },
                limit=100,
                with_payload=True,
                with_vectors=False
            )

            # Extract payloads
            payloads = [point.payload for point in scroll_result[0]]

            return Response({
                "start_time": today_start,
                "end_time": now_time,
                "count": len(payloads),
                "results": payloads
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def fetch_alerts_from_qdrant():
    logs = []
    logs.append("🔁 Fetching alerts from Qdrant")

    qdrant_client = QdrantClient(host="13.127.210.74", port=6333)

    local_tz = get_current_timezone()
    now = datetime.now(local_tz)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone().isoformat()
    now_time = now.astimezone().isoformat()
    cutoff_time = now - timedelta(hours=5)

    collections = qdrant_client.get_collections().collections
    for collection in collections:
        collection_name = collection.name
        logs.append(f"🔍 Checking Qdrant collection: {collection_name}")

        try:
            parts = collection_name.split("_")
            if len(parts) < 2 or not parts[1]:
                logs.append(f"⚠️ Invalid collection name format: {collection_name}")
                continue

            client_id = parts[1]
            logs.append(f"🔍 Processing client ID: {client_id}")
            try:
                #client = Client.objects.get(id=client_id)
                client = Client.objects.get(id="518fb02b-13ec-4bbe-ab83-9f242b8b1f30")
            except Client.DoesNotExist:
                logs.append(f"⚠️ No client found with ID {client_id}")
                continue
            print(f"🔍 Processing client ID: {client_id}")
            scroll_result = qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=None,
        #          scroll_filter={
        #             "must": [
        #                 {
        #                     "key": "timestamp",
        #                     "range": {
        #                         "gte": today_start,
        #                         "lte": now_time
        #                     }
        #                 }
        #     ]
        # },
                limit=1000,
                with_payload=True,
                with_vectors=False
            )
           # print("🔄 Scroll result fetched successfully++++++++++++++++++++++++++++", scroll_result)

            points = scroll_result[0]
            if not points:
                logs.append(f"⚠️ No points returned for collection {collection_name}")
                continue
            logs.append(f"🔄 Scroll returned {len(points)} points.")

            for point in points:
                payload = point.payload
                timestamp_str = payload.get("timestamp")
                if not timestamp_str:
                    logs.append(f"⚠️ No timestamp in point for client {client.id}")
                    continue

                try:
                    detection_time = isoparse(timestamp_str)
                except Exception:
                    logs.append(f"⚠️ Invalid timestamp format: {timestamp_str}")
                    continue

                # if detection_time < cutoff_time:
                #     logs.append(f"⏳ Skipping old point: {detection_time}")
                #     continue

                camera_id = payload.get("camera_id")
                labels = payload.get("classes", [])
                
               
                #valid_alert_types = AlertTypeMaster.objects.filter(domain=client.domain)
                valid_alert_types = AlertTypeMaster.objects.filter(id__in=ClientUseCase.objects.filter(client=client.id).values_list("usecase_id", flat=True)).distinct()
                print(f"🔍 Valid alert types for client {client.id}: {[at.type for at in valid_alert_types]}")
                valid_labels = set(valid_alert_types.values_list("type", flat=True))
                matching_labels = set(labels).intersection(valid_labels)
               # print(f"🔍 Matching labels for point: {matching_labels}")

                # if not matching_labels:
                #     logs.append(f"⚠️ No matching labels for client {client.id} in point {point.id}")
                #     print(f"⚠️ No matching labels for client {client.id} in point {point.id}")
                #     continue

                try:
                    camera = Camera.objects.get(id="e929fba6-8d7c-47a4-a1f8-89fc958e168b") 
                    #camera = Camera.objects.get(id=camera_id) 

                except Camera.DoesNotExist:
                    logs.append(f"⚠️ Camera not found: {camera_id}")
                    print(f"⚠️ Camera not found: {camera_id}")
                    continue

                user_profile = getattr(camera, "user_profile", None)
               

                for label in matching_labels:
                    print(f"🔍 Processing label: {label}")
                    logs.append(f"🔍 Processing label: {label}")
                    # alert_type = valid_alert_types.filter(type=label).first()
                    # if not alert_type:
                    #     print(f"⚠️ No alert type found for label: {label}")
                    #     #logs.append(f"⚠️ No alert type found for label: {label}")
                    #     continue
                    # else:
                    #     logs.append(f"⚠️ No alert type found for label: {label}")
                    #     print(f"🔍 Found alert type: {alert_type.name} for label: {label}")

                    # if Alert.objects.filter(camera=camera, label=label, timestamp=detection_time).exists():
                    #     continue
                    # usecase = ClientUseCase.objects.filter(client=client).first()
                    # if  usecase:
                    #     print(f"🔍 Use case found for client {client.id}: {usecase}")
                    alert_type = valid_alert_types.filter(type=label).first()
                    if not alert_type:
                        logs.append(f"⚠️ No alert type found for label '{label}' in domain '{client.domain}'")
                        continue
                    logs.append(f"🔍 Found alert type: {alert_type.name} for label: {label}")

                    # Check if this alert already exists
                    if Alert.objects.filter(camera=camera, label=label, timestamp=detection_time).exists():
                        logs.append(f"ℹ️ Duplicate alert skipped: {label} at {detection_time}")
                        continue
                    # Get the use case (severity mapping)
                    usecase = ClientUseCase.objects.filter(client=client, usecase=alert_type).first()
                    if not usecase:
                        logs.append(f"⚠️ No use case mapping for client {client.id} and alert type '{alert_type.type}'")
                        continue

                    logs.append(f"🔍 Use case found: {usecase.usecase} with severity {usecase.severity} for client {client.id}")
                    with transaction.atomic():
                        alert = Alert.objects.create(
                            owner=client,
                            camera=camera,
                            # user=user_profile,
                            usecase=usecase,
                            label=label,
                            timestamp=detection_time,
                            chunk_url=payload.get("chunk_m3u8_url", ""),
                            frame_url=payload.get("s3_url_image", "")
                        )
                        logs.append(f"✅ Alert saved: Client {client.id}, Label '{label}'")
                        
                        if usecase.severity and usecase.severity.lower() == "critical":
                            logs.append(f"🚨 Critical severity triggered for label '{label}' — invoking handler")
                            print(f"🚨🚨🚨 Critical severity triggered for label '{label}' — invoking handler")
                            #trigger_critical_action(alert)

        except Exception as e:
            logs.append(f"❌ Error processing collection {collection_name}: {str(e)}")

    return logs 
        
class FetchAlertsAPIView(APIView):
    def get(self, request):
        try:
            result = fetch_alerts_from_qdrant()
            return Response({"status": "success", "details": result}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
"""
@author: Neha Pawar
@date: 2025-07-21
@description: This view fetches alerts grouped by label and hour for a specific camera on a given date.
"""
class GroupedAlertsView(APIView):
    serializer_class = AlertTypeMasterSerializer
    # permission_classes = [IsAuthenticated]
    def get(self, request):
        camera_id = request.query_params.get('camera_id')
        date_str = request.query_params.get('date')

        if not date_str or not camera_id:
            return Response({"error": "camera_id and date are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        # Base queryset
        alerts = Alert.objects.filter(timestamp__date=date_obj, camera_id=camera_id)

        # Grouping by label, hour and picking first per hour
        grouped = defaultdict(dict)
        for alert in alerts.order_by('label', 'timestamp'):
            label = alert.label
            hour = alert.timestamp.replace(minute=0, second=0, microsecond=0)
            if hour not in grouped[label]:  # Only take the first alert per hour
                grouped[label][hour] = alert

        # Final response structure
        response = {}
        for label, hour_alerts in grouped.items():
            response[label] = []
            for alert in hour_alerts.values():
                response[label].append({
                    "id": str(alert.id),
                    "chunk_url": alert.chunk_url,
                    "date": alert.timestamp,
                    "eventType": label,
                    "thumbnail_url": alert.frame_url,
                    "cameraName": alert.camera.name if alert.camera else "Unknown",
                    "zoneName": alert.camera.assigned_zone.name if alert.camera and alert.camera.assigned_zone else "Unknown"
                })

        return Response(response, status=status.HTTP_200_OK)
    

"""
@author: Neha Pawar
@date: 2025-07-21
@description: This view fetches all alert types for a specific client.
"""
class ClientAlertTypesAPIView(generics.ListAPIView):
    serializer_class = AlertTypeMasterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        try:
            client = user.company_id
        except AttributeError:
            return AlertTypeMaster.objects.none() 

        return AlertTypeMaster.objects.filter(
            id__in=ClientUseCase.objects.filter(client=client).values_list("usecase_id", flat=True)
        ).distinct()