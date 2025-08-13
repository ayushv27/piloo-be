from celery import shared_task
from core.models import Alert, Client
from core.decorators import log_execution
from django.utils.timezone import now
from django.utils import timezone
from datetime import timedelta, datetime
from .utils import (
    send_wa_alert_template_notification,
    send_wa_report_template_notification,
    generate_pdf_report,
    generate_pdf_report_alerts,
    send_alert_email,
    send_delayed_alerts

)

from django.utils.timezone import now

import logging
logger = logging.getLogger("analytics")

@shared_task
def notify_low_severity_alerts():
    send_delayed_alerts(severity="low", delay_minutes=15) #8 * 60

@shared_task
def notify_medium_severity_alerts():
    send_delayed_alerts(severity="medium", delay_minutes=10) #4 * 60

@shared_task
def notify_high_severity_alerts():
    send_delayed_alerts(severity="high", delay_minutes=5)


# @log_execution
# def get_latest_alert_per_label_send_message(alerts):
#     # Step 2: Get the most recent alert per label
#     latest_alerts_per_label = (
#         alerts.order_by("label", "-created_at")
#         .distinct("label")
#     )
#     print("In get_latest_alert_per_label_send_message")
#     for alert in latest_alerts_per_label:
#         to_number = alert.owner.phone
#         to_email = alert.owner.email
#         client_name = alert.owner.name
#         clip_url = alert.chunk_url
#         thumbnail_url = alert.frame_url
#         label = alert.label
#         severity = alert.usecase.severity if alert.usecase else 'medium'
#         zone_name = alert.camera.assigned_zone.name
#         camera_name = alert.camera.name

#         try:
#             timestamp = alert.timestamp
#             date_part, time_part = timestamp.split("T")
#             time_fixed = time_part.replace("-", ":", 2).replace("+00-00", "+00:00")
#             ts = f"{date_part}T{time_fixed}"
#             tp = datetime.fromisoformat(ts)
#         except:
#             tp = alert.created_at

#         alert_date = tp.strftime("%-d %b %y")
#         alert_time = tp.strftime("%H:%M")
#         if alert.owner.wa_notifications == True:
#             # send_wa_alert_template_notification(
#             #     to_number,
#             #     client_name,
#             #     clip_url,
#             #     thumbnail_url,
#             #     label,
#             #     alert_date,
#             #     alert_time,
#             #     zone_name,
#             #     camera_name,
#             # )

#             try:
#                 send_wa_alert_template_notification(
#                     to_number,
#                     client_name,
#                     clip_url,
#                     thumbnail_url,
#                     label,
#                     alert_date,
#                     alert_time,
#                     zone_name,
#                     camera_name,
#                 )
#                 succeeded = True
#             except ConnectTimeout as exc:
#                 logger.warning("WA timeout for alert %s: %s", alert.id, exc)
#             except Exception:
#                 logger.exception("WA failed for alert %s", alert.id)

#         print("Email notifications enabled:", alert.owner.email_notifications)
#         if alert.owner.email_notifications == True:
#             print("Sending email notification..............")
#             send_alert_email(
#                 to_email,
#                 client_name,
#                 severity,
#                 label,
#                 alert_date,
#                 alert_time,
#                 zone_name,
#                 camera_name,
#                 clip_url,
#                 thumbnail_url,
#             )
            
#     for alert in alerts:
#         alert.notification_sent = True
#         alert.save(update_fields=["notification_sent"])

# @log_execution
# @shared_task
# def notify_low_severity_alerts():
#     threshold_time = timezone.now() - timedelta(hours=8)
#     alerts = Alert.objects.filter(
#         usecase__severity="low", notification_sent=False, created_at__lte=threshold_time
#     )
#     if not alerts.exists():
#         return
#     get_latest_alert_per_label_send_message(alerts)
        
        
        
# @log_execution
# @shared_task
# def notify_medium_severity_alerts():
#     threshold_time = timezone.now() - timedelta(hours=4)
#     alerts = Alert.objects.filter(
#         usecase__severity="medium", notification_sent=False, created_at__lte=threshold_time
#     )
#     if not alerts.exists():
#         return
#     get_latest_alert_per_label_send_message(alerts)



# @log_execution
# @shared_task
# def notify_high_severity_alerts():
#     # threshold_time = timezone.now() - timedelta(minutes=15)
#     threshold_time = timezone.now() - timedelta(minutes=15)
#     alerts = Alert.objects.filter(
#         usecase__severity="high", notification_sent=False, created_at__lte=threshold_time
#     )
#     if not alerts.exists():
#         return
    
#     get_latest_alert_per_label_send_message(alerts)
    

@log_execution
@shared_task
def send_scheduled_reports():
    current_time = now()

    def should_send(client):
        if not client.last_report_sent:
            return True

        delta = current_time - client.last_report_sent

        if client.report_frequency == "hourly":
            return delta >= timedelta(hours=1)
        elif client.report_frequency == "daily":
            return delta >= timedelta(days=1)
        elif client.report_frequency == "weekly":
            return delta >= timedelta(weeks=1)
        elif client.report_frequency == "biweekly":
            return delta >= timedelta(weeks=2)
        elif client.report_frequency == "monthly":
            return delta >= timedelta(days=30)
            # return delta >= relativedelta(months=1)
        return False

    clients = Client.objects.all()
    for client in clients:
        if should_send(client):
            print(f"Sending report to {client.name} ({client.email})")
            to_number = client.phone
            client_name = client.name

            # Send report notification
            report_url = generate_pdf_report(client.id)
            #report_url = generate_pdf_report_alerts(client.id)
            
            send_wa_report_template_notification(to_number, client_name, report_url)

            client.last_report_sent = current_time
            client.save(update_fields=["last_report_sent"])

