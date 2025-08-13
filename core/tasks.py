from celery import shared_task
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger("core")

@shared_task
def send_onboard_email(user_email, user_passsword):
    print("In send_onboard_email")
    context = {
        'user_email': user_email,
        'user_password': user_passsword
    }
    html_message = render_to_string('new_onboard_mail.html', context)
    plain_message = strip_tags(html_message)
    try:
        send_mail(
            subject="Welcome to Piloo.ai - Stop Watching, Start Asking.",
            message=plain_message,            
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message
        )
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user_email}: {e}")
        raise e
    
    
"""
@author: Neha Pawar
@date: 25-06-2025
@description: Celery tasks for sending emails, including OTP for email verification and password reset requests.
"""
# logger = logging.getLogger("core")

@shared_task
def send_email_otp(email, otp):
    try:
        html_content = render_to_string('emails/email_verification_otp.html', {'otp': otp})
        text_content = f'Your OTP code is {otp}. It is valid for 10 minutes.'

        subject = 'Your email verification OTP'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient = [email]

        email_message = EmailMultiAlternatives(subject, text_content, from_email, recipient)
        email_message.attach_alternative(html_content, "text/html")
        email_message.send(fail_silently=False)
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {e}")
        raise e
    

    
@shared_task
def send_password_reset_email(user_email, reset_url):
    context = {
        'reset_url': reset_url,
        'valid_hours': 24,
    }

    html_message = render_to_string('emails/password_reset.html', context)
    plain_message = render_to_string('emails/password_reset.txt', context)
    try:
        
        send_mail(
            subject="Password Reset Request",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message
        )
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user_email}: {e}")
        raise e
    
"""
@author: Mandar More
@date: 08-07-2025
@description: Celery task to expire subscriptions for clients whose subscription end date is less than today.
"""
@shared_task
def expire_subscriptions():
    from core.models import Client
    today = timezone.now().date()
    expired_client = Client.objects.filter(subscription_ends_at__lt=today, subscription_status='active')

    for client in expired_client:
        client.subscription_status = 'expired'
        # Note : Need discussion on whether to deactivate the subscription plan or not
        # client.subscription_plan__is_active = False
        client.save()
        logger.info(f"Client {client.name} subscription expired and deactivated.")


"""
@author: Mandar More
@date: 08-07-2025
@description: Celery task to send subscription expiry notification to users of clients whose subscription is expiring in 3 days.
"""
@shared_task
def send_subscription_expiry_notification():

    from core.models import Client, UserProfile

    try:
        target_date = timezone.now().date() + timedelta(days=3)
        clients = Client.objects.filter(subscription_ends_at=target_date, subscription_status='active')
        
        if not clients.exists():
            logger.info("No clients with subscriptions expiring in 3 days.")
            return
       
        for client in clients:

            users = UserProfile.objects.filter(company=client, is_active=True).exclude(email__isnull=True)
            
            for user in users:
                
                context = {
                    'client_name': client.name,
                    'user_name': user.username or user.email.split('@')[0],
                    'subscription_end_date': client.subscription_ends_at
                }

                subject = "Your Subscription is Expiring Soon"

                # "Note : DEFAULT_FROM_EMAIL key is missing in settings.py, please add it to send emails"
                
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient = [user.email]

                html_content = render_to_string('emails/subscription_expiry_notification.html', context)
                text_content = (
                    f"Dear {context['user_name']},\n\n"
                    f"Your organization's subscription ({context['client_name']}) will expire on {context['subscription_end_date']}.\n"
                    f"Please renew it to continue uninterrupted service.\n\n"
                    f"Best regards,\nPiloo Team"
                )

                email_message = EmailMultiAlternatives(subject, text_content, from_email, recipient)
                email_message.attach_alternative(html_content, "text/html")
                email_message.send(fail_silently=False)

                logger.info(f"Sent expiry notification to {user.email}")

    except Exception as e:
        logger.error(f"Failed to send subscription expiry notification: {e}")


