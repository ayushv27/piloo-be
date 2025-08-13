
# Signal handlers for automatic model updates
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import *
from .tasks import send_onboard_email
from .decorators import log_execution
# import secrets
# temp_password = secrets.token_urlsafe(10)




@log_execution
@receiver(post_save, sender=Client)
def default_client_user(sender, instance, created, **kwargs):
    """Create Userprofile model when a new Client is created"""
    print('client is created.. user is being created')
    if created:
        password = 'piloo'
        user = UserProfile.objects.create_user(
            email=instance.email,
            phone=instance.phone if instance.phone else None,
            password= password,
            role="company_admin",
            company=instance,
            is_active=True,
            is_verified=True,
        )
        send_onboard_email.delay(instance.email, password)


@receiver(post_save, sender=UserProfile)
def create_user_profile(sender, instance, created, **kwargs):
    """Create related models when a new user is created"""
    if created:
        OnboardingProgress.objects.create(
            user=instance, onboarding_started=timezone.now()
        )
        MenuPermission.objects.create(user=instance)
        SystemSettings.objects.create(user=instance)


# @receiver(pre_save, sender=Alert)
# def update_alert_timestamps(sender, instance, **kwargs):
#     """Update alert timestamps based on status changes"""
#     if instance.pk:
#         try:
#             old_instance = Alert.objects.get(pk=instance.pk)
#             if old_instance.status != instance.status:
#                 if instance.status == "resolved" and not instance.resolved_at:
#                     instance.resolved_at = timezone.now()
#         except Alert.DoesNotExist:
#             pass


# # @receiver(post_save, sender=Alert)
# # def create_alert_notification(sender, instance, created, **kwargs):
# #     """Create notification when new alert is generated"""
# #     if created and instance.usecase.severity in ["high", "critical"]:
# #         Notification.objects.create(
# #             company=instance.owner.name,
# #             type="alert",
# #             priority=instance.usecase.severity,
# #             title=f"New {instance.usecase.severity} Alert",
# #             message=f"{instance.get_type_display()} detected at {instance.camera.location}",
# #             data={"alert_id": instance.id, "camera_id": instance.camera.id},
# #         )


        

# @receiver(post_save, sender=DemoRequest)
# def demo_request_user(sender, instance, created, **kwargs):
#     """Create related model when a new Demo Request Received is created"""
#     if created:
#         UserProfile.objects.create(
#             email=instance.email,
#             phone=instance.phone if instance.phone else None,
#             role="demo",
#             is_active=True,
#             is_verified=True,
#         )
        
        
