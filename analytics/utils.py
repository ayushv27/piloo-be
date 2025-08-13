from datetime import datetime 
from matplotlib import pyplot as plt
import os
from django.conf import settings
from pathlib import Path
import httpx
from core.models import Alert, Client, Report
import json
from urllib.parse import urlparse
from .report_utils import generate_single_pdf, merge_pdfs
from django.db.models import Count
from core.decorators import log_execution
from django.utils.timezone import now
from core.utils import get_cdn_url
from django.utils.timezone import now
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging
from pytz import timezone
from collections import Counter
from datetime import timedelta
from django.utils.timezone import now

from django.utils.timezone import localtime

logger = logging.getLogger("analytics")
import boto3

twilio_account_sid = settings.TWILIO_ACCOUNT_SID
twilio_auth_token = settings.TWILIO_AUTH_TOKEN
twilio_whatsapp_number = settings.TWILIO_WHATSAPP_NUMBER
twilio_message_sid = settings.TWILIO_MESSAGE_SID
alert_template_sid = settings.ALERT_TEMPLATE_CONTENT_SID
report_template_sid = settings.REPORT_TEMPLATE_CONTENT_SID

s3 = boto3.client("s3", aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

def create_pie_chart(pie_data):
    labels = list(pie_data.keys())
    sizes = list(pie_data.values())
    colors = ['#0F0773', '#4B179D', '#8B2FAE'][:len(labels)]  

    plt.figure(figsize=(8, 8))
    
    # plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140)
    
    wedges, texts, autotexts = plt.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        colors=colors,
        startangle=140,
        pctdistance=0.7
    )

    # Add legend using the same labels and colors
    plt.legend(
        wedges,
        labels,
        title="Alert Types",
        loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1)
    )

    plt.title('Alert Distribution by Event Type')
    plt.tight_layout()

    pie_path = os.path.abspath("templates/alert_pie_chart.png")
    plt.savefig(pie_path)
    plt.close()

    print(f"Pie chart saved at: {pie_path}")
    return pie_path


def create_heat_map(camera_events):
    camera_names = []
    intrusion_counts = []
    mask_missing_counts = []
    motion_detected_counts = []

    for camera_data in camera_events:
        for camera_name, events in camera_data.items():
            camera_names.append(camera_name)
            intrusion_counts.append(events.get("Fire", 0))
            mask_missing_counts.append(events.get("POB", 0))
            motion_detected_counts.append(events.get("TOP", 0))

    x = range(len(camera_names))
    plt.figure(figsize=(12, 12))

    plt.bar(x, intrusion_counts, label='Fire', color='#4B179D')
    plt.bar(x, mask_missing_counts, bottom=intrusion_counts, label='POB', color='#C2417B')
    bottom2 = [i + m for i, m in zip(intrusion_counts, mask_missing_counts)]
    plt.bar(x, motion_detected_counts, bottom=bottom2, label='TOP', color='#F59E0B')

    plt.xlabel('Cameras')
    plt.ylabel('Event Count')
    plt.title('Alert Events per Camera (Stacked)')
    plt.xticks(ticks=x, labels=camera_names, rotation=45)
    plt.legend()
    plt.tight_layout()

    bar_path = os.path.abspath("templates/alert_stacked_chart.png")
    plt.savefig(bar_path)
    plt.close()
    print(f"Stacked chart saved at: {bar_path}")
    
    return bar_path

def get_highest_alert(camera_events):
    max_count = 0
    max_camera = None
    max_alert_type = None

    for camera_data in camera_events:
        for camera_name, alerts in camera_data.items():
            for alert_type, count in alerts.items():
                if count > max_count:
                    max_count = count
                    max_camera = camera_name
                    max_alert_type = alert_type

    return max_camera, max_alert_type

def get_most_frequent_alert_per_camera(camera_events):
    most_frequent_alerts = {}

    for camera_data in camera_events:
        for camera_name, alerts in camera_data.items():
            if alerts:
                most_common_alert = max(alerts.items(), key=lambda x: x[1])  # (alert_type, count)
                most_frequent_alerts[camera_name] = {
                    "alert_type": most_common_alert[0],
                    "count": most_common_alert[1]
                }

    return most_frequent_alerts



def get_file_key(file_url):
    parsed = urlparse(file_url)
    return parsed.path.lstrip("/")


@log_execution
def send_wa_alert_template_notification(to_number, client_name, clip_url, thumbnail_url, label, alert_date, alert_time, zone_name, camera_name):
    try:
        # Optional: check if clip URL is accessible
        with httpx.Client(timeout=5.0) as client:
            img_response = client.head(clip_url)
            if img_response.status_code != 200:
                raise Exception(f"Clip URL not accessible: {img_response.status_code}")

        url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/Messages.json"
        thumbnail_path = get_file_key(thumbnail_url)
        print('thumbnail_path', thumbnail_path)
        content_variables = {
            "1": client_name,
            "2": label,
            "3": alert_date,
            "4": alert_time,
            "5": zone_name,
            "6": camera_name,
            "7": clip_url,
            "8": thumbnail_path
        }

        data = {
            "To": f"whatsapp:{to_number}",
            "From": twilio_whatsapp_number,  
            "MessagingServiceSid": twilio_message_sid,
            "ContentSid": alert_template_sid,  # your approved template SID
            "ContentVariables": json.dumps(content_variables)
        }
        
        print('alert_data', data)

        with httpx.Client() as client:
            response = client.post(
                url,
                data=data,
                auth=(twilio_account_sid, twilio_auth_token),
            )

        response_data = response.json()
        print(f"Twilio Response for alert: {response.status_code}-{response_data}")

        if response.status_code != 201:
            raise Exception(f"Failed to send WhatsApp message: {response.status_code} - {response.text}")

        return response_data

    except Exception as e:
        print(f"Error sending WhatsApp alert: {str(e)}")
        raise
    
    
@log_execution
def send_wa_report_template_notification(to_number, client_name, report_url):
    try:
        # Optional: check if clip URL is accessible
        with httpx.Client(timeout=5.0) as client:
            img_response = client.head(report_url)
            if img_response.status_code != 200:
                raise Exception(f"Clip URL not accessible: {img_response.status_code}")

        url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/Messages.json"
        report_path = get_file_key(report_url)
        content_variables = {
            "1": client_name,
            "2": report_url,
            "3": report_path,
        }

        data = {
            "To": f"whatsapp:{to_number}",
            "From": twilio_whatsapp_number,  
            "MessagingServiceSid": twilio_message_sid,
            "ContentSid": report_template_sid, 
            "ContentVariables": json.dumps(content_variables)
        }

        print('report_data', data)
        with httpx.Client() as client:
            response = client.post(
                url,
                data=data,
                auth=(twilio_account_sid, twilio_auth_token),
            )

        response_data = response.json()
        print(f"Twilio Response for report: {response.status_code} -{response_data}")

        if response.status_code != 201:
            raise Exception(f"Failed to send WhatsApp message: {response.status_code} - {response.text}")

        return response_data

    except Exception as e:
        print(f"Error sending WhatsApp alert: {str(e)}")
        raise
  
def get_start_time_for_frequency(frequency):
    now_time = now()
    if frequency == "hourly":
        return now_time - timedelta(hours=1)
    elif frequency == "daily":
        return now_time - timedelta(days=1)
    elif frequency == "weekly":
        return now_time - timedelta(weeks=1)
    elif frequency == "biweekly":
        return now_time - timedelta(weeks=2)
    elif frequency == "monthly":
        return now_time - timedelta(days=30)  # Can use relativedelta(months=1) if needed
    return now_time - timedelta(days=1)  # default fallback  


@log_execution
def generate_pdf_report(client_id):
    
        try:
            client = Client.objects.get(id=client_id)
            report_frequency = client.report_frequency.upper() 
            # start_time = get_start_time_for_frequency(client.report_frequency)
            # alerts = Alert.objects.filter(owner_id=client_id, timestamp__gte=start_time)
 
            alerts = Alert.objects.filter(owner_id=client_id)
            print(alerts)
            hour_counter = Counter()
            for alert in alerts:
                ist_time = alert.timestamp.astimezone(timezone("Asia/Kolkata"))
                hour = ist_time.hour  # 0–23
                hour_counter[hour] += 1

            peak_incidence_time = None
            peak_incidence_count = 0

            if hour_counter:
                peak_hour, peak_incidence_count = hour_counter.most_common(1)[0]
                peak_incidence_time = datetime.strptime(str(peak_hour), "%H").strftime("%I %p")

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

            # for row in camera_alerts:
            #     camera_id = row['camera__id']
            #     if camera_id not in seen:
            #         seen.add(camera_id)
            for alert in pie_data_qs:
                latest_alert = Alert.objects.filter(label=alert['label']).order_by('-timestamp').select_related('camera').first()
                    # )
                    # latest_alert = (
                    #     Alert.objects.filter(camera_id=camera_id, label=row['label'])
                    #     .order_by('-timestamp')
                    #     .select_related('camera')
                    #     .first()
                    # )
                    

                if latest_alert:
                    ist_time = latest_alert.timestamp.astimezone(timezone("Asia/Kolkata"))
                    alert_cards.append({
                        "image_url": latest_alert.frame_url,
                        "alert_type": latest_alert.label.replace("_", " ").title(),
                        "camera_name": latest_alert.camera.name,
                        "location": latest_alert.camera.location,
                        # "timestamp": latest_alert.timestamp,
                        # "date": latest_alert.timestamp.strftime("%Y-%m-%d"),
                        # "time": latest_alert.timestamp.strftime("%H:%M:%S"),
                        "date": ist_time.strftime("%d-%m-%Y"),       
                         "time": ist_time.strftime("%I:%M %p"), 
                    })

            min_timestamp = alerts.order_by("timestamp").values_list("timestamp", flat=True).first()
            max_timestamp = alerts.order_by("-timestamp").values_list("timestamp", flat=True).first()

            if min_timestamp and max_timestamp:
                if min_timestamp.year == max_timestamp.year:
                    if min_timestamp.month == max_timestamp.month:
                        # Same month and year
                        report_period = min_timestamp.strftime("%B %Y")  # e.g., "July 2025"
                    else:
                        # Same year, different months
                        report_period = f"{min_timestamp.strftime('%B')} - {max_timestamp.strftime('%B')}"  # e.g., "June - July 2025"
                else:
                    # Different years
                    report_period = f"{min_timestamp.strftime('%B')} - {max_timestamp.strftime('%B')}"  # e.g., "Dec 2024 - Jan 2025"
            else:
                report_period = "N/A"

            most_common_label = None
            if pie_data_qs:
                most_common_label = max(pie_data_qs, key=lambda x: x["count"])["label"]
                most_common_label = most_common_label.replace("_", " ").title()  


            context = {
                "client_name": client.name,
                "report_period": report_period,
                "report_frequency": report_frequency,
                "plan": client.subscription_plan.name,
                "total_events": client.client_alerts.count(),
                # "total_events": alerts.count(),
                "max_camera": max_camera,
                "max_alert_type": max_alert_type,
                "most_frequent_alerts": result,
                "alert_cards": alert_cards,
                "active_cameras": client.cameras.count(),
                "pie_chart_path": os.path.join(settings.MEDIA_URL, pie_path),
                "stack_path": os.path.join(settings.MEDIA_URL, stack_path),
                # "month": report_period,
                "most_common": most_common_label,  
                "peak_incidence_time": peak_incidence_time,
            }
            print("context :", context)
            
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
                raise print(f"Missing HTML files: {', '.join(missing_files)}")

            # Convert each HTML to PDF bytes
            pdf_bytes_list = []
            for html_file in html_files:
                try:
                    print('generating single pdf')
                    pdf_bytes = generate_single_pdf(html_file, base_url, context)
                    pdf_bytes_list.append(pdf_bytes)
                except Exception as e:
                    print(f"Failed to generate PDF for {html_file}: {str(e)}")

            # Merge PDFs
            try:
                print('Trying to store report...')

                # Generate a safe filename with no colons or spaces
                timestamp = now().strftime('%Y%m%d_%H%M%S')
                filename = f"Report_{client_id}_{timestamp}.pdf"
                s3_path = f"reports/{filename}"
                local_path = os.path.join('media', filename)  # /tmp/Report_xxx.pdf

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
                print('file uploaded to s3')
                # Step 2: Upload to S3 via Django FileField
                # with open(local_path, 'rb') as f:
                # django_file = File(f)  # ✅ Wrap in Django File object
                report = Report.objects.create(client_id=client_id, report=s3_path)
                    # report.report.save(s3_path, f)

                # Step 3: Clean up local file
                # if os.path.exists(local_path):
                #     os.remove(local_path)

                # Step 4: Return the S3/CDN URL
                report_url = get_cdn_url(report.report.name)
                print('Uploaded report to:', report_url)
                return report_url

            except Exception as e:
                print(f"Failed to merge/store PDF: {str(e)}")
                return None
        except Exception as e:
                print(f"PDF generation failed: {str(e)}")
                return None
        
def get_alert_cards_for_report(client_id, limit=10):
    # alerts = (
    #     Alert.objects.filter(owner_id=client_id)
    #     .select_related("camera")
    #     .order_by("-timestamp")[:limit]
    # )
    alerts = Alert.objects.all()
    print("✅✅These are the alerts", alerts)

    alert_cards = []
    for alert in alerts:
        alert_cards.append({
            "image_url": alert.frame_url,
            "label": alert.label,
            #"severity": alert.severity,
            "camera_name": alert.camera.name if alert.camera else "Unknown",
            "location": alert.camera.location if alert.camera else "Unknown",
            "timestamp": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return alert_cards


ALERTS_PER_PAGE = 3
import math
from weasyprint import HTML



@log_execution
def generate_pdf_report_alerts(client_id):
    try:
        print(f"🔍 Starting PDF generation for client: {client_id}")
        client = Client.objects.get(id=client_id)
        alert_cards = get_alert_cards_for_report(client_id)
        print("✅✅These are the alerts", alert_cards)
        print("✅ Total alerts fetched:", len(alert_cards))
        alerts = Alert.objects.filter(owner_id=client_id)
        pie_data_qs = alerts.values("label").annotate(count=Count("id"))
        camera_data_qs = alerts.values("camera__name", "label").annotate(count=Count("id"))

        camera_events_dict = {}

        for entry in camera_data_qs:
            camera = entry["camera__name"]
            label = entry["label"]
            count = entry["count"]
            if camera not in camera_events_dict:
                camera_events_dict[camera] = {}
            camera_events_dict[camera][label] = count

        camera_events = [{cam: data} for cam, data in camera_events_dict.items()] if camera_events_dict else []

        if camera_events:
            max_camera, max_alert_type = get_highest_alert(camera_events)
            result = get_most_frequent_alert_per_camera(camera_events)
        else:
            max_camera = None
            max_alert_type = None
            result = []

        context_base = {
           
            "client_name": client.name,
            "report_period": "June 2025 - July 2025",
            "plan": client.subscription_plan.name,
            "total_events": client.client_alerts.count(),
            "max_camera": max_camera,
            "max_alert_type": max_alert_type,
            "most_frequent_alerts": result,
            "alert_cards": alert_cards,
            "active_cameras": client.cameras.count(),
        }

        base_dir = Path(__file__).resolve().parent.parent
        templates_dir = os.path.join(base_dir, "templates")
        pdf_bytes_list = []

        # 1. Start page
        start_path = os.path.join(templates_dir, "index.html")
        try:
            print("📄 Rendering start page...")
            pdf_bytes_list.append(generate_single_pdf(start_path, base_dir, context_base))
        except Exception as e:
            print(f"❌ Error rendering start.html: {e}")
            raise

        # 2. Alert pages
        total_alerts = len(alert_cards)
        total_pages = math.ceil(total_alerts / ALERTS_PER_PAGE)

        print(f"📄 Generating {total_pages} alert pages...")
        for page_num in range(total_pages):
            start = page_num * ALERTS_PER_PAGE
            end = start + ALERTS_PER_PAGE
            page_alerts = alert_cards[start:end]

            context = {**context_base, "alerts": page_alerts, "page_number": page_num + 1}
            alert_page_path = os.path.join(templates_dir, "alerts.html")

            try:
                pdf_bytes_list.append(generate_single_pdf(alert_page_path, base_dir, context))
                print(f"✅ Page {page_num + 1} rendered with {len(page_alerts)} alerts")
            except Exception as e:
                print(f"❌ Error rendering alert page {page_num + 1}: {e}")
                raise
        # ✅ No pagination — render all alerts together
        # alert_page_path = os.path.join(templates_dir, "alerts.html")
        # context = {**context_base, "alerts": alert_cards}

        # try:
        #     print(f"📄 Rendering all alerts ({len(alert_cards)}) in one go...")
        #     pdf_bytes_list.append(generate_single_pdf(alert_page_path, base_dir, context))
        # except Exception as e:
        #     print(f"❌ Error rendering alerts.html: {e}")
        #     raise


        # 3. End page
        end_path = os.path.join(templates_dir, "index4.html")
        try:
            print("📄 Rendering end page...")
            pdf_bytes_list.append(generate_single_pdf(end_path, base_dir, context_base))
        except Exception as e:
            print(f"❌ Error rendering end.html: {e}")
            raise

        # 4. Merge PDFs
        timestamp = now().strftime('%Y%m%d_%H%M%S')
        filename = f"Report_{client_id}_{timestamp}.pdf"
        local_path = os.path.join('media', filename)
        s3_path = f"reports/{filename}"

        merge_pdfs(pdf_bytes_list, local_path)
        print("✅ PDF merged and saved locally")
        s3.upload_file(
                    Filename=local_path,
                    Bucket=settings.S3_BUCKET, 
                    Key=s3_path,
                    ExtraArgs={
                        "ContentType": "application/pdf", 
                        "CacheControl": "no-cache"
                    }
                )

        print("📤 Uploaded PDF to S3")

        report = Report.objects.create(client_id=client_id, report=s3_path)
        report_url = get_cdn_url(report.report.name)
        print("📄 Report created:", report_url)
        return report_url

    except Exception as e:
        print(f"🔥 PDF generation failed: {e}")
        return None
    
    

#not in use anymore,as Meta needs a template 
def send_whatsapp_report_notification(to_number, client_name, report_url):

    # # Verify image URL is accessible
    try:
        with httpx.Client() as client:
            img_response = client.head(report_url)
            if img_response.status_code != 200:
                raise Exception(f"Image URL not accessible: {img_response.status_code}")
    except Exception as e:
        print(f"Error checking image URL: {str(e)}")
        return

    url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/Messages.json"
    data = {
        "From": twilio_whatsapp_number,
        "To": f"whatsapp:{to_number}",
        "Body": (
    f"📊 *Weekly Surveillance Report*\n\n"
    f"Dear {client_name},\n\n"
    "Your weekly activity summary from the Piloo Monitoring System is now available.\n\n"
    "This report includes:\n"
    "• Detected alerts and incidents\n"
    "• Top 4 incident frames\n"
    "• Camera activity summary & statistics\n\n"
    f"📑 *Download Report (PDF):* {report_url}\n\n"
    "This is an automated message. Please *do not reply* to this number.\n\n"
    "Best regards,\n"
    "Team Piloo.ai"
),
    "MediaUrl": report_url

    }

    try:
        with httpx.Client() as client:
            response = client.post(
                url,
                data=data,
                auth=(twilio_account_sid, twilio_auth_token),
            )

            response_data = response.json()
            print(f"Full Twilio Response: {response_data}")

            if response.status_code != 201:
                raise Exception(
                    f"Failed to send WhatsApp message: {response.status_code} {response.text}"
                )

            # Monitor message status
            message_sid = response_data.get('sid')
            if message_sid:
                # Check message status after a delay
                status_url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/Messages/{message_sid}.json"
                status_response = client.get(
                    status_url,
                    auth=(twilio_account_sid, twilio_auth_token),
                )
                status_data = status_response.json()
                if status_data.get('status') == 'failed':
                    print(f"Error Code: {status_data.get('error_code')}")
                    print(f"Error Message: {status_data.get('error_message')}")            
    except Exception as e:
        print(f"Exception in send_whatsapp_report_notification: {str(e)}")
        raise
    
    
    
#not in use 
# twilio API manager
def send_whatsapp_alert_notification(to_number, client_name, clip_url, thumbnail_url, label, alert_date, alert_time, zone_name, camera_name):
    
    # Verify image URL is accessible
    try:
        with httpx.Client() as client:
            img_response = client.head(clip_url)
            if img_response.status_code != 200:
                raise Exception(f"Clip URL not accessible: {img_response.status_code}")
    except Exception as e:
        print(f"Error checking image URL: {str(e)}")
        return

    url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/Messages.json"
    data = {
        "From": twilio_whatsapp_number,
        "To": f"whatsapp:{to_number}",
        "Body": (
        f"🔔 *Security Alert Notification*\n\n"
        f"Dear {client_name},\n\n"
        "An alert has been triggered by your surveillance system.\n\n"
        f"*Alert Type:* {label}\n"
        f"*Date:* {alert_date}\n"
        f"*Time:* {alert_time}\n"
        f"*Location:* {zone_name} - {camera_name}\n\n"
        f"🎥 *View Alert Clip:* {clip_url}\n\n"
        "This is an automated notification from the Piloo.ai Safety Monitoring System.\n"
        "Please *do not reply* to this message.\n\n"
        "Stay safe,\n"
        "Team Piloo.ai"),
        "MediaUrl": thumbnail_url
        
    }

    try:
        with httpx.Client() as client:
            response = client.post(
                url,
                data=data,
                auth=(twilio_account_sid, twilio_auth_token),
            )

            response_data = response.json()
            print(f"Full Twilio Response: {response_data}")

            if response.status_code != 201:
                raise Exception(
                    f"Failed to send WhatsApp message: {response.status_code} {response.text}"
                )

            # Monitor message status
            message_sid = response_data.get('sid')
            if message_sid:
                # Check message status after a delay
                status_url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/Messages/{message_sid}.json"
                status_response = client.get(
                    status_url,
                    auth=(twilio_account_sid, twilio_auth_token),
                )
                print(f"Message Status after 5s: {status_response.json().get('status')}")
                status_data = status_response.json()
                print(f"Message Status: {status_data.get('status')}")
                if status_data.get('status') == 'failed':
                    print(f"Error Code: {status_data.get('error_code')}")
                    print(f"Error Message: {status_data.get('error_message')}")
            
    except Exception as e:
        print(f"Exception in send_whatsapp_alert_notification: {str(e)}")
        raise


def  send_alert_email(
    to_email, client_name, severity, label, alert_date, alert_time, zone_name, camera_name, clip_url, thumbnail_url):
    
    print("Send alert mail")
    label = label
    context = {
        "client_name": client_name,
        "label": label,
        "alert_date": alert_date,
        "alert_time": alert_time,
        "zone_name": zone_name,
        "camera_name": camera_name,
        "clip_url": clip_url,
        "thumbnail_url": thumbnail_url,
        "severity": severity.capitalize(),  # Ensure severity is capitalized
    }
    try:
        print("label :", label)
        html_message = render_to_string("new_email_alerts.html", context)
        plain_message = strip_tags(html_message)   
    except Exception as e:
        logger.error(f"Failed to render template: {e}")
        raise e
    try:
        send_mail(
            # subject=f"[{severity} Severity Alert] - {label}",
            subject= f"[{severity.capitalize()} Severity Alert] - Notification from Piloo.ai - {label}",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_message,
        )
        print("Email sent successfully to", to_email)
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        raise e




def  send_medium_severity_alerts_email(
    to_email, client_name, label, alert_date, alert_time, zone_name, camera_name, clip_url, thumbnail_url):
    
    context = {
        "client_name": client_name,
        "label": label,
        "alert_date": alert_date,
        "alert_time": alert_time,
        "zone_name": zone_name,
        "camera_name": camera_name,
        "clip_url": clip_url,
        "thumbnail_url": thumbnail_url,
    }
    html_message = render_to_string("medium_severity_alert.html", context)
    plain_message = strip_tags(html_message)   

    try:
        send_mail(
            subject=f"[Medium Severity Alert] - {label}",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_message,
        )
        print("Email sent successfully to", to_email)
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        raise e



def generate_pdf_report_by_date(client_id, date):
    
        try:
            client = Client.objects.get(id=client_id)
            report_frequency = client.report_frequency.upper()  

            alerts = Alert.objects.filter(owner_id=client.id, timestamp__date=date)
            print(alerts)
            hour_counter = Counter()
            for alert in alerts:
                ist_time = alert.timestamp.astimezone(timezone("Asia/Kolkata"))
                hour = ist_time.hour  # 0–23
                hour_counter[hour] += 1

            peak_incidence_time = None
            peak_incidence_count = 0

            if hour_counter:
                peak_hour, peak_incidence_count = hour_counter.most_common(1)[0]
                peak_incidence_time = datetime.strptime(str(peak_hour), "%H").strftime("%I %p")
           
            pie_data_qs = alerts.values("label").annotate(count=Count("id"))
            pie_data = {entry["label"]: entry["count"] for entry in pie_data_qs}
 
            #print('pie_data', pie_data)
            
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

           # print('camera_events', camera_events)
            
            stack_path = create_heat_map(camera_events)
            max_camera, max_alert_type = get_highest_alert(camera_events)
            result = get_most_frequent_alert_per_camera(camera_events)
           # print('result', result)
            camera_alerts = (
            Alert.objects.values('camera__id', 'camera__name', 'camera__location', 'label', 'usecase__usecase__type')
            .annotate(alert_count=Count('id'))
            .order_by('camera__id', '-alert_count')
            )

            # Organize by camera, keeping the top alert type per camera
            seen = set()
            alert_cards = []

            # for row in camera_alerts:
            #     camera_id = row['camera__id']
            #     if camera_id not in seen:
            #         seen.add(camera_id)
            for alert in pie_data_qs:
                latest_alert = Alert.objects.filter(label=alert['label']).order_by('-timestamp').select_related('camera').first()
                    # )
                    # latest_alert = (
                    #     Alert.objects.filter(camera_id=camera_id, label=row['label'])
                    #     .order_by('-timestamp')
                    #     .select_related('camera')
                    #     .first()
                    # )
                    

                if latest_alert:
                    ist_time = latest_alert.timestamp.astimezone(timezone("Asia/Kolkata"))

                    alert_cards.append({
                        "image_url": latest_alert.frame_url,
                        "alert_type": latest_alert.label.replace("_", " ").title(),
                        "camera_name": latest_alert.camera.name,
                        "location": latest_alert.camera.location,
                        "date": ist_time.strftime("%d-%m-%Y"),       
                        "time": ist_time.strftime("%I:%M %p"), 
                        
                    })

            min_timestamp = alerts.order_by("timestamp").values_list("timestamp", flat=True).first()
            max_timestamp = alerts.order_by("-timestamp").values_list("timestamp", flat=True).first()

            # if min_timestamp and max_timestamp:
            #     if min_timestamp.year == max_timestamp.year:
            #         if min_timestamp.month == max_timestamp.month:
            #             # Same month and year
            #             report_period = min_timestamp.strftime("%B %Y")  # e.g., "July 2025"
            #         else:
            #             # Same year, different months
            #             report_period = f"{min_timestamp.strftime('%B')} - {max_timestamp.strftime('%B')}"  # e.g., "June - July 2025"
            #     else:
            #         # Different years
            #         report_period = f"{min_timestamp.strftime('%B')} - {max_timestamp.strftime('%B')}"  # e.g., "Dec 2024 - Jan 2025"
            # else:
            #     report_period = "N/A"  
            if isinstance(date, str):
                date = datetime.strptime(date, "%Y-%m-%d").date()
            report_period = date.strftime("%B %d, %Y")
            # month = date.strftime("%B")  
            most_common_label = None
            if pie_data_qs:
                most_common_label = max(pie_data_qs, key=lambda x: x["count"])["label"]
                most_common_label = most_common_label.replace("_", " ").title()
           # print('most_common_label==============================', most_common_label)


            context = {
                "client_name": client.name,
                "report_period": report_period,
                "report_frequency": report_frequency,
                "plan": client.subscription_plan.name,
                "total_events": client.client_alerts.count(),
                "max_camera": max_camera,
                "max_alert_type": max_alert_type,
                "most_frequent_alerts": result,
                "alert_cards": alert_cards,
                "active_cameras": client.cameras.count(),
                "pie_chart_path": os.path.join(settings.MEDIA_URL, pie_path),
                "stack_path": os.path.join(settings.MEDIA_URL, stack_path),
                "most_common": most_common_label,  
                "peak_incidence_time": peak_incidence_time,
            }
            print("context :", context)
            
            # List of HTML files to convert
            base_url = Path(__file__).resolve().parent.parent
            html_files = [
                os.path.join(base_url, "templates/report_page1.html"),
                os.path.join(base_url, "templates/report_page2.html"),
                os.path.join(base_url, "templates/report_page3.html"),
               
            ]

            # Check file existence
            missing_files = [f for f in html_files if not os.path.exists(f)]
            if missing_files:
                raise print(f"Missing HTML files: {', '.join(missing_files)}")

            # Convert each HTML to PDF bytes
            pdf_bytes_list = []
            for html_file in html_files:
                try:
                    print('generating single pdf')
                    pdf_bytes = generate_single_pdf(html_file, base_url, context)
                    pdf_bytes_list.append(pdf_bytes)
                except Exception as e:
                    print(f"Failed to generate PDF for {html_file}: {str(e)}")

            # Merge PDFs
            try:
                print('Trying to store report...')

                # Generate a safe filename with no colons or spaces
                timestamp = now().strftime('%Y%m%d_%H%M%S')
                filename = f"Report_{client_id}_{timestamp}.pdf"
                s3_path = f"reports/{filename}"
                local_path = os.path.join('media', filename)  # /tmp/Report_xxx.pdf

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
                print('file uploaded to s3')
                # Step 2: Upload to S3 via Django FileField
                # with open(local_path, 'rb') as f:
                # django_file = File(f)  # ✅ Wrap in Django File object
                report = Report.objects.create(client_id=client_id, report=s3_path)
                    # report.report.save(s3_path, f)

                # Step 3: Clean up local file
                # if os.path.exists(local_path):
                #     os.remove(local_path)

                # Step 4: Return the S3/CDN URL
                report_url = get_cdn_url(report.report.name)
                print('Uploaded report to:', report_url)
                return report_url

            except Exception as e:
                print(f"Failed to merge/store PDF: {str(e)}")
                return None
        except Exception as e:
                print(f"PDF generation failed: {str(e)}")
                return None
        
        
def get_latest_alert_per_label_send_message(alerts):
    latest_alerts_per_label = (
        alerts.order_by("label", "-created_at").distinct("label")
    )

    for alert in latest_alerts_per_label:
        owner = alert.owner
        # try:
        #     timestamp = alert.timestamp
        #     if "T" in timestamp:
        #         date_part, time_part = timestamp.split("T")
        #         time_fixed = time_part.replace("-", ":", 2).replace("+00-00", "+00:00")
        #         ts = f"{date_part}T{time_fixed}"
        #         tp = datetime.fromisoformat(ts)
        #     else:
        #         tp = alert.created_at
        # except:
        #     tp = alert.created_at

        # alert_date = tp.strftime("%-d %b %y")
        # alert_time = tp.strftime("%H:%M")
        ist_time = localtime(alert.timestamp)  
        alert_date = ist_time.strftime('%-d %b %Y')      
        alert_time = ist_time.strftime('%I:%M %p')  

        context = {
            "to_number": owner.phone,
            "to_email": owner.email,
            "client_name": owner.name,
            "clip_url": alert.chunk_url,
            "thumbnail_url": alert.frame_url,
            "label": alert.label.replace("_", " ").title(),
            "severity": alert.usecase.severity if alert.usecase else 'medium',
            "zone_name": alert.camera.assigned_zone.name,
            "camera_name": alert.camera.name,
            "alert_date": alert_date,
            "alert_time": alert_time,
        }

        # WhatsApp
        if owner.wa_notifications:
            try:
                send_wa_alert_template_notification(
                    context["to_number"],
                    context["client_name"],
                    context["clip_url"],
                    context["thumbnail_url"],
                    context["label"],
                    context["alert_date"],
                    context["alert_time"],
                    context["zone_name"],
                    context["camera_name"],
                )
                logger.info(f"📲 WA sent for alert {alert.id}")
            except ConnectTimeout as exc:
                logger.warning(f"⚠️ WA timeout for alert {alert.id}: {exc}")
            except Exception:
                logger.exception(f"❌ WA failed for alert {alert.id}")

        # Email
        if owner.email_notifications:
            try:
                send_alert_email(
                    context["to_email"],
                    context["client_name"],
                    context["severity"],
                    context["label"],
                    context["alert_date"],
                    context["alert_time"],
                    context["zone_name"],
                    context["camera_name"],
                    context["clip_url"],
                    context["thumbnail_url"],
                )
                logger.info(f"📧 Email sent for alert {alert.id}")
            except Exception:
                logger.exception(f"❌ Email failed for alert {alert.id}")

    # Mark all as sent
    alerts.update(notification_sent=True)

        
        


def send_delayed_alerts(severity: str, delay_minutes: int):
    threshold_time = now() - timedelta(minutes=delay_minutes)
    alerts = Alert.objects.filter(
        usecase__severity=severity,
        notification_sent=False,
        created_at__lte=threshold_time
    )
    if alerts.exists():
        get_latest_alert_per_label_send_message(alerts)
