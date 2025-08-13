import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "piloo.settings")

app = Celery("piloo")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()




# app.conf.beat_schedule = {
#     'check-every-minute': {
#         'task': 'analytics.tasks.check_rtsp_streams_nginx',
#         'schedule': crontab(minute='*/300'),
#     },
#     'expire-subscriptions': {
#         'task': 'core.tasks.expire_subscriptions',
#         'schedule': crontab(hour=0, minute=0),  # Runs daily at midnight
#     },
#     'send_subscription_expiry_notification': {
#         'task': 'core.tasks.send_subscription_expiry_notification',
#         'schedule': crontab(hour=0, minute=0),  # Runs daily at midnight
#     },

# }

app.conf.beat_schedule = {
    'fetch-alerts-every-2-mins': {
        'task': 'event_alerts.tasks.fetch_and_store_alerts_result',
        'schedule': crontab(minute='*/2'), # Runs every 2 minutes
    },
    'sync-recordings-every-hour': {
        'task': 'camera.tasks.sync_all_cameras_recordings_from_s3',
        # 'schedule': crontab(hour=0),  # Runs at the start of every hour
        'schedule': crontab(minute='*/5'), # Runs every 5 minutes for testing

    },
}

