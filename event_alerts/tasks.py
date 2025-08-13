from celery import shared_task
from core.models import (
    UserProfile,
    Alert,
    Camera,
    AlertTypeMaster,
    Client,
    ClientUseCase,
)
from datetime import datetime, time
from django.utils import timezone
from datetime import timedelta
from qdrant_client import QdrantClient
from django.db import transaction
from django.utils.timezone import get_current_timezone
import requests
import logging
from qdrant_client import QdrantClient
from analytics.tasks import send_alert_email
import pytz
from dateutil.parser import isoparse
from analytics.utils import send_wa_alert_template_notification
from django.core.cache import cache
from django.utils.timezone import get_current_timezone, now
from django.utils.timezone import localtime


logger = logging.getLogger("event_alerts")


# @shared_task
# def fetch_and_store_alerts_result():
   
#     print("🔁🔁 Fetching alerts from Qdrant")
#     qdrant_client = QdrantClient(host="15.206.181.97", port=6333)

#     local_tz = get_current_timezone()
#     now = datetime.now(local_tz)
#     today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone().isoformat()
#     now_time = now.astimezone().isoformat()
#     cutoff_time = now - timedelta(minutes=3)

#     collections = qdrant_client.get_collections().collections
#     for collection in collections:
#         collection_name = collection.name
#         #print(f"🔍 Checking Qdrant collection: {collection_name}")

#         try:
#             parts = collection_name.split("_")
#             if len(parts) < 2 or not parts[1]:
#                 #print(f"⚠️ Invalid collection name format: {collection_name}")
#                 continue

#             client_id = parts[1]
#             #print(f"🔍 Processing client ID: {client_id}")
#             try:
#                 client = Client.objects.get(id=client_id)
#             except Client.DoesNotExist:
#                 #print(f"⚠️ No client found with ID {client_id}")
#                 continue
#            # print(f"🔍 Processing client ID: {client_id}")
#             scroll_result = qdrant_client.scroll(
#                 collection_name=collection_name,
#                 #scroll_filter=None,
#                 scroll_filter={
#                             "must": [
#                                 {
#                                     "key": "timestamp",
#                                     "range": {
#                                         "gte": today_start,
#                                         "lte": now_time
#                                     }
#                                 }
#                     ]
#                 },
#                 limit=1000,
#                 with_payload=True,
#                 with_vectors=False
#             )
#            # print("🔄 Scroll result fetched successfully++++++++++++++++++++++++++++", scroll_result)

#             points = scroll_result[0]
#             if not points:
#                 #print(f"⚠️ No points returned for collection {collection_name}")
#                 continue
#             #print(f"🔄 Scroll returned {len(points)} points.")

#             for point in points:
#                 payload = point.payload
#                 timestamp_str = payload.get("timestamp")
#                 if not timestamp_str:
#                    # print(f"⚠️ No timestamp in point for client {client.id}")
#                     continue

#                 try:
#                     detection_time = isoparse(timestamp_str)
#                 except Exception:
#                     logger.error(f"⚠️ Invalid timestamp format: {timestamp_str}")
#                     #print(f"⚠️ Invalid timestamp format: {timestamp_str}")
#                     continue

#                 # if detection_time < cutoff_time:
#                 #     print(f"⏳ Skipping old point: {detection_time}")
#                 #     continue

#                 camera_id = payload.get("camera_id")
#                 labels = payload.get("classes", [])
                
#                 valid_alert_types = AlertTypeMaster.objects.filter(id__in=ClientUseCase.objects.filter(client=client.id).values_list("usecase_id", flat=True)).distinct()

#                 #print(f"🔍 Valid alert names for client {client.id}: {[at.name for at in valid_alert_types]}")
#                 valid_labels = set(valid_alert_types.values_list("name", flat=True))
#                 matching_labels = set(labels).intersection(valid_labels)
#                 #print(f" 🔍 🔍 🔍 Matching labels for point: {matching_labels}")

#                 if not matching_labels:
#                     logger.info(f"⚠️ No matching labels for client {client.id} in point {point.id}")
#                     #print(f"⚠️ No matching labels for client {client.id} in point {point.id}")
#                     continue

#                 try:
#                     #camera = Camera.objects.get(id="e929fba6-8d7c-47a4-a1f8-89fc958e168b") 
#                      camera = Camera.objects.get(id=camera_id) 

#                 except Camera.DoesNotExist:
#                     logger.error(f"⚠️ Camera not found: {camera_id}")
#                    # print(f"⚠️ Camera not found: {camera_id}")
#                     continue

#                 for label in matching_labels:
#                     print(f"🔍 Processing label: {label}")
#                     logger.info(f"🔍 Processing label: {label}")
                   
#                     alert_type = valid_alert_types.filter(name=label).first()
#                     if not alert_type:
#                        # print(f"⚠️ ⚠️⚠️⚠️No alert type found for label '{label}' in domain '{client.domain}'")
#                         logger.info(f"⚠️ No alert type found for label '{label}' in domain '{client.domain}'")
#                         continue
#                    # print(f"🔍 Found alert name : {alert_type.name} for label: {label}")

#                     # Check for duplicate alerts in the last 2 minutes
#                     time_threshold = detection_time - timedelta(minutes=2)
#                     if Alert.objects.filter(
#                         camera=camera,
#                         label=label,
#                         timestamp__gte=time_threshold,
#                         timestamp__lte=detection_time,
#                     ).exists():
#                         #print(f"⏩ Skipping duplicate alert for label '{label}' from camera '{camera.id}' in last 2 mins")
#                         continue

#                     # Get the use case (severity mapping)
#                     usecase = ClientUseCase.objects.filter(client=client, usecase=alert_type).first()
#                     if not usecase:
#                         logger.info(f"⚠️ No use case mapping for client {client.id} and alert type '{alert_type.type}'")
#                        # print(f"⚠️ No use case mapping for client {client.id} and alert type '{alert_type.type}'")
#                         continue

#                    # print(f"🔍 Use case found: {usecase.usecase} with severity {usecase.severity} for client {client.id}")
#                     with transaction.atomic():
#                        # print(f"⏳⏳⏳⏳⏳⏳⏳⏳⏳Trying to create alert for client {client.id} with label '{label}' at {detection_time}, severity: {usecase.severity}")
#                         alert = Alert.objects.create(
#                             owner=client,
#                             camera=camera,
#                             usecase=usecase,
#                             label=label,
#                             timestamp=detection_time,
#                             chunk_url=payload.get("chunk_m3u8_url", ""),
#                             frame_url=payload.get("s3_url_image", "")
#                         )
#                         logger.info(f"✅ Alert saved: Client {client.id}, Label '{label}'")
#                        # print(f"✅ Alert saved: Client {client.id}, Label '{label}'")
                       
#     #added by Devina                   
#     #adding temporary logic to hold critical event for 5 mins, send notifications email/ whats app as per client set up
#                         # if usecase.severity == "critical":
#                         #     logger.info(f"Critical severity triggered for label '{label}' — invoking handler")
#                         #     recent_sent = alert.notification_sent

#                         #     if recent_sent:
#                         #         logger.info(f"Skipping notification for label '{label}' — already sent in last 5 minutes")
#                         #     else:
#                         #         alert_date = alert.timestamp.strftime('%Y-%m-%d')
#                         #         alert_time = alert.timestamp.strftime('%H:%M:%S')
#                         #         if client.wa_notifications == True:
#                         #             send_wa_alert_template_notification(
#                         #                 client.phone,
#                         #                 client.name,
#                         #                 alert.chunk_url,
#                         #                 alert.frame_url,
#                         #                 alert.label,
#                         #                 alert_date,
#                         #                 alert_time,
#                         #                 alert.camera.assigned_zone.name,
#                         #                 alert.camera.name
#                         #             )
#                         #         if client.email_notifications == True:
#                         #             send_alert_email(
#                         #                             client.email,
#                         #                             client.name,
#                         #                             usecase.severity,
#                         #                             label,
#                         #                             alert_date,
#                         #                             alert_time,
#                         #                             alert.camera.assigned_zone.name,
#                         #                             alert.camera.name,
#                         #                             alert.chunk_url,
#                         #                             alert.frame_url,
#                         #                         )
#                         #         alert.notification_sent = True
#                         #         alert.save(update_fields=["notification_sent"])
#                         if usecase.severity.lower() == "critical":
#                             logger.info(f"Critical severity triggered for label '{label}' — invoking handler")
#                             print(f"Critical severity triggered for label '{label}' — invoking handler")
                          
#                             # Check if any alert was sent in the last 5 minutes for the same label and camera
#                             recent_alert_exists = Alert.objects.filter(
#                                 camera=alert.camera,
#                                 label=alert.label,
#                                 usecase__severity="critical",
#                                 notification_sent=True,
#                                 timestamp__gte=timezone.now() - timedelta(minutes=5)
#                             ).exists()

#                             if not recent_alert_exists:
#                                 alert_date = alert.timestamp.strftime('%Y-%m-%d')
#                                 alert_time = alert.timestamp.strftime('%H:%M:%S')

#                                 if client.wa_notifications:
#                                     print(f"Sending WhatsApp notification for critical alert:================ {alert.label}")

#                                     send_wa_alert_template_notification(
#                                         client.phone,
#                                         client.name,
#                                         alert.chunk_url,
#                                         alert.frame_url,
#                                         alert.label,
#                                         alert_date,
#                                         alert_time,
#                                         alert.camera.assigned_zone.name,
#                                         alert.camera.name
#                                     )

#                                     alert.notification_sent = True
#                                     alert.save(update_fields=["notification_sent"])
#                                 if client.email_notifications:
#                                      send_alert_email(
#                                                     client.email,
#                                                     client.name,
#                                                     usecase.severity,
#                                                     label,
#                                                     alert_date,
#                                                     alert_time,
#                                                     alert.camera.assigned_zone.name,
#                                                     alert.camera.name,
#                                                     alert.chunk_url,
#                                                     alert.frame_url,
#                                                 )

#                             else:
#                                 logger.info(f"🚫 Skipping duplicate critical alert for label '{alert.label}' on camera '{alert.camera.name}'")


#                                 print(f"🚫 Skipping duplicate critical alert for label '{alert.label}' on camera '{alert.camera.name}'" )                            

#         except Exception as e:
#             logger.error(f"❌ Error processing collection {collection_name}: {str(e)}")

#            # print(f"❌ Error processing collection {collection_name}: {str(e)}")





LOCK_EXPIRE = 60 * 5  # 5 minutes

@shared_task
def fetch_and_store_alerts_result():
    lock_id = "fetch_and_store_alerts_lock"
    if cache.get(lock_id):
        logger.info("🔒 Task already running, skipping duplicate execution.")
        return
    cache.set(lock_id, True, LOCK_EXPIRE)

    try:
        logger.info("🔁 Fetching alerts from Qdrant")
        qdrant_client = QdrantClient(host="15.206.181.97", port=6333)

        local_tz = get_current_timezone()
        current_time = datetime.now(local_tz)
        today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0).astimezone().isoformat()
        now_time = current_time.astimezone().isoformat()

        collections = qdrant_client.get_collections().collections

        for collection in collections:
            collection_name = collection.name
            parts = collection_name.split("_")
            if len(parts) < 2 or not parts[1]:
                continue

            client_id = parts[1]
            try:
                client = Client.objects.get(id=client_id)
            except Client.DoesNotExist:
                continue

            try:
                scroll_result = qdrant_client.scroll(
                    collection_name=collection_name,
                    scroll_filter={
                        "must": [
                            {
                                "key": "timestamp",
                                "range": {
                                    "gte": today_start,
                                    "lte": now_time
                                }
                            }
                        ]
                    },
                    limit=1000,
                    with_payload=True,
                    with_vectors=False
                )

                points = scroll_result[0]
                if not points:
                    continue

                valid_alert_types = AlertTypeMaster.objects.filter(
                    id__in=ClientUseCase.objects.filter(client=client.id).values_list("usecase_id", flat=True)
                ).distinct()
                valid_labels = set(valid_alert_types.values_list("name", flat=True))

                for point in points:
                    payload = point.payload
                    timestamp_str = payload.get("timestamp")
                    if not timestamp_str:
                        continue

                    try:
                        detection_time = isoparse(timestamp_str)
                    except Exception:
                        logger.warning(f"⚠️ Invalid timestamp format: {timestamp_str}")
                        continue

                    camera_id = payload.get("camera_id")
                    labels = payload.get("classes", [])

                    matching_labels = set(labels).intersection(valid_labels)
                    if not matching_labels:
                        continue

                    try:
                        camera = Camera.objects.get(id=camera_id)
                    except Camera.DoesNotExist:
                        logger.warning(f"⚠️ Camera not found: {camera_id}")
                        continue

                    for label in matching_labels:
                        alert_type = valid_alert_types.filter(name=label).first()
                        if not alert_type:
                            continue

                        usecase = ClientUseCase.objects.filter(client=client, usecase=alert_type).first()
                        if not usecase:
                            continue

                        time_threshold = detection_time - timedelta(minutes=2)
                        if Alert.objects.filter(
                            camera=camera,
                            label=label,
                            timestamp__gte=time_threshold,
                            timestamp__lte=detection_time,
                        ).exists():
                            print(f"⏩ Skipping duplicate alert for label '{label}' from camera '{camera.id}' in last 2 mins")
                            continue

                        # Deduplicate with get_or_create using timestamp + camera + label
                        try:
                            with transaction.atomic():
                                alert, created = Alert.objects.get_or_create(
                                    owner=client,
                                    camera=camera,
                                    label=label,
                                    timestamp=detection_time,
                                    defaults={
                                        "usecase": usecase,
                                        "chunk_url": payload.get("chunk_m3u8_url", ""),
                                        "frame_url": payload.get("s3_url_image", ""),
                                    }
                                )

                                if created:
                                    logger.info(f"✅ New alert saved for Client {client.name}[{client.id}], Label '{label}'")
                                else:
                                    logger.info(f"⏭️ Alert already exists for Client {client.name}[{client.id}], Label '{label}' at {detection_time}")
                                    continue

                                # Handle notifications only for critical alerts
                                if usecase.severity.lower() == "critical":
                                    recent_alert = Alert.objects.filter(
                                        camera=alert.camera,
                                        label=alert.label,
                                        usecase__severity="critical",
                                        timestamp__gte=now() - timedelta(minutes=5)
                                    ).order_by('-timestamp').first()

                                    if recent_alert and recent_alert.notification_sent:
                                        logger.info(f"🚫 Skipping duplicate notification for label '{label}'")
                                        continue

                                    ist_time = localtime(alert.timestamp)  
                                    alert_date = ist_time.strftime('%-d %b %Y')      
                                    alert_time = ist_time.strftime('%I:%M %p')      

                                    if client.wa_notifications:
                                        logger.info(f"📲 Sending WhatsApp notification for critical alert '{label}'")
                                        send_wa_alert_template_notification(
                                            client.phone,
                                            client.name,
                                            alert.chunk_url,
                                            alert.frame_url,
                                            alert.label,
                                            alert_date,
                                            alert_time,
                                            alert.camera.assigned_zone.name,
                                            alert.camera.name
                                        )
                                        alert.notification_sent = True

                                    if client.email_notifications:
                                        logger.info(f"📧 Sending email alert for critical alert '{label}'")
                                        send_alert_email(
                                            client.email,
                                            client.name,
                                            usecase.severity,
                                            label,
                                            alert_date,
                                            alert_time,
                                            alert.camera.assigned_zone.name,
                                            alert.camera.name,
                                            alert.chunk_url,
                                            alert.frame_url
                                        )
                                        alert.notification_sent = True

                                    alert.save(update_fields=["notification_sent"])

                        except Exception as e:
                            logger.error(f"❌ Failed to save alert or send notification: {str(e)}")

            except Exception as e:
                logger.error(f"❌ Error processing collection {collection_name}: {str(e)}")

    finally:
        cache.delete(lock_id)
