from core.models import Camera, Recording
from django.conf import settings
from datetime import datetime, timedelta
from celery import shared_task, group
import boto3
import logging
import os 

logger = logging.getLogger(__name__)


@shared_task
def sync_all_cameras_recordings_from_s3(days_to_check=2):
    camera_ids = Camera.objects.values_list('id', flat=True)
    job = group(sync_camera_recordings_from_s3.s(camera_id, days_to_check) for camera_id in camera_ids)
    result = job.apply_async()

    logger.info("Launched parallel tasks for all cameras.")
    return f"Launched {len(camera_ids)} camera sync tasks."


@shared_task
def sync_camera_recordings_from_s3(camera_id, days_to_check=2):    

    try:
        camera = Camera.objects.get(id=camera_id)
        logger.info(f"Processing camera ID {camera.id}: {camera.name}")
    except Camera.DoesNotExist:
        logger.warning(f"Camera {camera_id} not found.")
        return f"Camera {camera_id} not found"

    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.REGION_NAME,
    )

    today = datetime.now().date()  
    total_inserted = 0

    for day_offset in range(days_to_check):
        date = today - timedelta(days=day_offset)
        prefix = os.path.join('streams/recordings', str(camera.id), str(date))

        logger.info(f"Checking recordings for camera {camera.name} on {date} with prefix {prefix}")

        try:
            paginator = s3.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=settings.S3_BUCKET, Prefix=prefix)
        except Exception as e:
            logger.error(f"S3 access error for camera {camera.id} on {date}: {str(e)}")
            return f"Error accessing S3 for camera {camera.id}: {e}"

        bulk_objects = []
        for page in pages:
            for item in page.get("Contents", []):
                key = item["Key"]
                if not key.endswith(".mp4"):
                    continue

                parts = key.split("/")
                if len(parts) < 6:
                    continue

                date_str = parts[3]  # e.g., "2025-08-01"
                hour_str = parts[4]  # e.g., "11"
                filename = parts[5]
                # url = f"{settings.CDN_DOMAIN}/{key}"
                url = f"{settings.CDN_DOMAIN.rstrip('/')}/{key.lstrip('/')}"


                try:
                    start_time = datetime.strptime(f"{date_str} {hour_str}", "%Y-%m-%d %H")
                except ValueError:
                    logger.warning(f"Could not parse datetime from key: {key}")
                    continue

                if Recording.objects.filter(camera=camera, filename=filename, start_time=start_time).exists():
                    continue

                bulk_objects.append(Recording(
                    camera=camera,
                    filename=filename,
                    file_path=url,
                    start_time=start_time,
                    end_time=start_time + timedelta(minutes=15),
                    duration=timedelta(minutes=15),
                    has_motion=False,
                    has_audio=False,
                    thumbnail_path=None,
                    cloud_url=url,
                    is_archived=False,
                    checksum=None,
                    metadata={},
                    owner=getattr(camera, "owner", None)
                ))

        if bulk_objects:
            Recording.objects.bulk_create(bulk_objects, ignore_conflicts=True)
            logger.info(f"{len(bulk_objects)} recordings inserted for camera {camera.name} on {date}")
            total_inserted += len(bulk_objects)
        else:
            logger.info(f"No new recordings found for camera {camera.name} on {date}")    
            
    logger.info(f"Finished processing camera {camera.name}. Total inserted: {total_inserted}")
    return f"{total_inserted} new recordings inserted for camera {camera.name}"
