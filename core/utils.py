import os
import boto3
from django.conf import settings
from botocore.client import Config
from django.template.loader import render_to_string
# from django.core.mail import send_mail
# from django.utils.html import strip_tags
# from django.template.loader import render_to_string
# from datetime import datetime
import socket
from urllib.parse import urlparse
from rest_framework_simplejwt.tokens import RefreshToken
from .tasks import send_password_reset_email  
import redis
import json


env_var = settings.ENV_VARIABLE


if env_var == 'local' or 'beast':
    s3 = None
else:
    s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, 
                          aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, 
                          region_name=settings.AWS_S3_REGION_NAME, config=Config(signature_version='s3v4'))

# def get_domain_url(file_name):  not usinf anywhere
#     return os.path.join(settings.DOMAIN_ROOT, file_name)

def get_cdn_url(file_name):
    cdn_url = os.path.join(settings.CDN_DOMAIN, file_name)
    return cdn_url


def generate_otp(length=6):
    if env_var == 'prod':
        otp = 112233
        # characters = string.digits
        # otp = ''.join(random.choice(characters) for _ in range(length))      #112233   
    else:
        otp = 112233
    return otp


def format_number(number: str, country_code: str = "91") -> str:
    number = number.strip().replace(" ", "").replace("-", "")
    if not number.startswith("+"):
        if number.startswith("0"):
            number = number[1:]
        number = f"+{country_code}{number}"
    return number


def get_tokens_for_user(user):
    return RefreshToken.for_user(user).access_token


def send_reset_email(user, reset_token, domain):
        #getting host domain to return link
            
        reset_url = f"{domain}/login/{reset_token.token}"
        print(reset_url, 'reset_url')
        # send email using celery task
        send_password_reset_email.delay(user.email, reset_url)




def is_rtsp_reachable(rtsp_url, timeout=3):
    print('inside is_rtsp_reachable()')
    try:
        parsed = urlparse(rtsp_url)
        host = parsed.hostname
        port = parsed.port or 1935
        print('host', host, 'port', port)
        with socket.create_connection((host, port), timeout=timeout):
            print('RTSP stream is live', rtsp_url)
            return True
    except Exception:
        print("rtsp stream has stopped", rtsp_url)
        return False
    
    

def is_rtmp_live(url, timeout=3):
    print('inside is_rtmp_live')
    # Parse host and port from RTMP URL like: rtmp://host:port/live/stream
    try:
        host = url.split("//")[1].split("/")[0].split(":")[0]
        port = int(url.split("//")[1].split("/")[0].split(":")[1])
    except Exception:
        return False

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False
    

redis_client = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

# def publish_status_change(camera_id, status):
#     message = json.dumps({
#         "camera_id": str(camera_id),
#         "status": status
#     })
#     redis_client.publish("camera_status_updates", message)
    
                                
# def publish_alert_update(alert_instance):
#     from camera.serializers import AlertSSENotificationSerializer  # or your appropriate serializer

#     alert_data = AlertSSENotificationSerializer(alert_instance).data
#     owner_id = alert_instance.owner.id

#     # Use per-owner Redis channel
#     redis_client.publish(f"alert_updates_owner_{owner_id}", json.dumps(alert_data))


# def broadcast_dashboard_update(user_id):
#     # redis_client.publish(f"dashboard_stats_{user.pk}", json.dumps({"update": True}))
#     redis_client.publish(
#         f"dashboard_stats_{user_id}", 
#         json.dumps({"update": True, "owner_id": str(user_id)})
    # )
    
    
