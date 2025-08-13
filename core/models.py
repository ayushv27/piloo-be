# ------------------------------------------------------------------------
# Copyright (c) 2025 Piloo.ai
#
# Piloo.ai - AI-Powered CCTV Monitoring Platform
# Copyright © 2025 Pyrack Solutions Pvt. Ltd.
# Website: https://pyrack.com/
# All rights reserved. Proprietary software.
# ------------------------------------------------------------------------

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import (
    RegexValidator,
    MinValueValidator,
    MaxValueValidator,
    URLValidator,
)
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from .managers import UserManager, custom_url_validator
import uuid
import os
from django.conf import settings


# from piloo_core import models
    
class Domain(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        db_table = "piloo_domains"
    
    def __str__(self):
        return self.name
  


class Client(models.Model):
    SUBSCRIPTION_STATUS = [
    ("active", "Active"),
    ("inactive", "Inactive"),
    ("trial", "Trial"),
    ("expired", "Expired"),
    ("cancelled", "Cancelled"),
]
    
    REPORT_FREQUENCY = [
    ('hourly', 'Hourly'),
    ("daily", "Daily"),
    ("weekly", "Weekly"),
    ("biweekly", "Bi-Weekly"),
    ("monthly", "Monthly"),
]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        validators=[RegexValidator(regex=r"^\+?1?\d{9,15}$")],
    )
    subscription_plan = models.ForeignKey(
        "SubscriptionPlan",
        on_delete=models.CASCADE,
        related_name="subscribed_plan",
        default=1,
    )
    report_frequency = models.CharField(
        max_length=20, choices=REPORT_FREQUENCY, default="daily"
    )
    report_hour = models.TimeField(default='17:00')
    subscription_status = models.CharField(
        max_length=20, choices=SUBSCRIPTION_STATUS, default="active"
    )
    # stripe_customer_id = models.CharField(max_length=100, null=True, blank=True)
    # stripe_subscription_id = models.CharField(max_length=100, null=True, blank=True)
    # max_cameras = models.IntegerField()
    subscription_ends_at = models.DateField(null=True, blank=True)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE)
    additional_recordings_storage = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(365)], default=0)
    additional_cameras = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(500)], default=0)
    recording_quality = models.CharField(max_length=10)
    retention_days = models.IntegerField(default=30, validators=[MinValueValidator(0)])
    email_notifications = models.BooleanField(default=False)
    wa_notifications = models.BooleanField(default=False)
    timezone = models.CharField(max_length=50, default="Asia/Kolkata")
    language = models.CharField(max_length=10, default="en")
    last_report_sent = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        if Client.objects.filter(name__iexact=self.name).exclude(pk=self.pk).exists():
            raise ValidationError(
                {"name": "This name already exists. Please choose a different name."}
            )
            
    def save(self, *args, **kwargs):
        self.full_clean()
        self.subscription_ends_at = timezone.now().date() + timedelta(days=self.subscription_plan.subscription_days)
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = "piloo_clients"

    def __str__(self):
        return f"{self.name}_{self.subscription_plan}"
    
    
    
class ClientNotificationsTo(models.Model):
    company = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    phone = models.CharField(max_length=16, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    
    class Meta:
        db_table = "piloo_client_notifications_to"



class UserProfile(AbstractUser):
    """Extended user model for Piloo.ai platform"""

    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("manager", "Manager"),
        ("viewer", "Viewer"),
        ("company_admin", "Company Admin"),
        ("demo", "Demo"),
    ]
    username = models.CharField(max_length=150, blank=True, null=True)

    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        validators=[RegexValidator(regex=r"^\+?1?\d{9,15}$")],
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="viewer")
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    company = models.ForeignKey(
        Client,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="client_users",
        help_text="The client this user belongs to.",
        verbose_name="clients",
    )

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="piloo_users",
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="piloo_user_permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def clean(self):
        if not self.email and not self.phone:
            raise ValidationError("Either email or phone must be set.")
        if not self.username:
            self.username = self.email or self.phone  # fallback default

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table = "piloo_users"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class MenuPermission(models.Model):
    """User menu permissions for feature access control"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE, related_name="menu_permissions"
    )
    dashboard = models.BooleanField(default=True)
    ai_chat = models.BooleanField(default=True)
    live_feed = models.BooleanField(default=True)
    recordings = models.BooleanField(default=True)
    alerts = models.BooleanField(default=True)
    employees = models.BooleanField(default=False)
    zones = models.BooleanField(default=True)
    reports = models.BooleanField(default=True)
    subscription = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "piloo_menu_permission"

    def __str__(self):
        return f"Permissions for {self.user.username}"


class PasswordResetToken(models.Model):
    """
    Manages password reset functionality with time-based token validation.
    Tokens expire after 24 hours and can only be used once.
    """

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)


class Zone(models.Model):
    """Monitoring zones for camera coverage areas"""

    ZONE_TYPES = [
        ("entrance", "Entrance"),
        ("office", "Office"),
        ("restricted", "Restricted"),
        ("common", "Common Area"),
        ("parking", "Parking"),
        ("warehouse", "Warehouse"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=ZONE_TYPES)
    description = models.TextField(blank=True)
    coordinates = models.JSONField(null=True, blank=True)  # For zone boundary mapping
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="zones", null=True, blank=True
    )
    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "piloo_zones"
        ordering = ["name"]
        unique_together = ["name", "owner"]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Camera(models.Model):
    """Camera configuration and management"""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("maintenance", "Maintenance"),
        ("offline", "Offline"),
        ("error", "Error"),
    ]

    QUALITY_CHOICES = [
        ("480p", "480p"),
        ("720p", "720p"),
        ("1080p", "1080p"),
        ("4K", "4K"),
    ]
    presets = [
        "Ultrafast",
        "Superfast",
        "Veryfast",
        "Faster",
        "Fast",
        "Medium",
        "Slow",
        "Slower",
        "Veryslow",
    ]
    PRESET_CHOICES = [(preset.lower(), preset) for preset in presets]

    frameRates = [15, 20, 24, 25, 30, 48, 50, 60]

    FRAMERATE_CHOICES = [(fr, fr) for fr in frameRates]

    video_bitrates = [
        "500k",  # Low quality
        "1000k",  # // Medium quality
        "2000k",  # // High quality
        "4000k",  # // Very high quality
        "8000k",  # // Ultra HD quality
    ]
    VIDEO_BITRATE_CHOICES = [(v_br, v_br) for v_br in video_bitrates]

    audio_bitrates = [
        "64k",  # Low quality
        "96k",  # Medium quality
        "128k",  # High quality
        "192k",  # Very high quality
        "256k",  # Lossless quality
    ]
    AUDEO_BITRATE_CHOICES = [(a_br, a_br) for a_br in audio_bitrates]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, null=True, blank=True)
    # ip_address = models.GenericIPAddressField(null=True, blank=True)
    rtsp_url = models.CharField(
        max_length=200,
        validators=[custom_url_validator],
        help_text="Accepts http, https, rtsp, rtmp schemes",
        null=True,
        blank=True,
    )
    last_check = models.DateTimeField(null=True, blank=True)
    rtmp_url = models.CharField(
        max_length=200,
        validators=[custom_url_validator],
        help_text="Accepts http, https, rtsp, rtmp schemes",
        null=True,
        blank=True,
    )
    hls_url = models.CharField(
        max_length=200,
        validators=[custom_url_validator],
        help_text="Accepts http, https, rtsp, rtmp schemes",
        null=True,
        blank=True,
    )
    output_url = models.CharField(
        max_length=200,
        validators=[custom_url_validator],
        help_text="Accepts http, https, rtsp, rtmp schemes",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    assigned_zone = models.ForeignKey(
        Zone,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="camera_zones",
    )
    sensitivity = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Motion detection sensitivity (1-10)",
    )
    recording_enabled = models.BooleanField(default=True)
    retention_days = models.IntegerField(default=30, validators=[MinValueValidator(1)])
    quality = models.CharField(max_length=10, choices=QUALITY_CHOICES, default="1080p")
    has_audio = models.BooleanField(default=False)
    pan_tilt_zoom = models.BooleanField(default=False)
    night_vision = models.BooleanField(default=False)
    outdoor_rated = models.BooleanField(default=False)
    preset = models.CharField(
        max_length=10, choices=PRESET_CHOICES, default="superfast"
    )
    framerate = models.IntegerField(choices=FRAMERATE_CHOICES, default=20)
    video_bitrate = models.CharField(
        max_length=10, choices=VIDEO_BITRATE_CHOICES, default="500k"
    )
    audio_bitrate = models.CharField(
        max_length=10, choices=AUDEO_BITRATE_CHOICES, default="96k"
    )
    mac_address = models.CharField(max_length=17, null=True, blank=True)
    firmware_version = models.CharField(max_length=50, null=True, blank=True)
    last_maintenance = models.DateTimeField(null=True, blank=True)
    uptime_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00
    )
    owner = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="cameras", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "piloo_cameras"
        ordering = ["name"]
        unique_together = ["name", "assigned_zone"]

    def __str__(self):
        return f"{self.name} - {self.owner.name}"

    def save(self, *args, **kwargs):
        # is_update = self.pk is not None and type(self).objects.filter(pk=self.pk).exists()
        if self.rtmp_url is None:
            self.rtmp_url = os.path.join(settings.RTMP_HOST, f"{self.owner.id}_{self.id}")
        self.hls_url = os.path.join(
            settings.CDN_DOMAIN, 'streams', str(self.owner.id), str(self.id), 'playlist.m3u8'
        )
        self.output_url = os.path.join(settings.CDN_DOMAIN, 'streams', 'hls', str(self.id), f"live_{self.id}.m3u8")
        # if is_update:
        #     pass
        # self.rtmp_url = f"{settings.RTMP_HOST}/{self.owner.id}_{self.id}"
        # self.hls_url = f"{settings.CDN_DOMAIN}/streams/{self.owner.id}/{self.id}/playlist.m3u8"
        # self.output_url = f"{settings.CDN_DOMAIN}/streams/playlist.m3u8"

        super().save(*args, **kwargs)
    
    
class AlertTypeMaster(models.Model):
    
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='model_alerts')
    type = models.CharField(max_length=50)
    name = models.CharField(max_length=150)
    # description = models.TextField()
    
    def __str__(self):
        return f"{self.type}-{self.name}"
    
    
    class Meta:
        db_table = "piloo_alert_type_master"
    
    
class ClientUseCase(models.Model):
    SEVERITY_LEVELS = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="usecases")
    usecase = models.ForeignKey(AlertTypeMaster, on_delete=models.CASCADE)
    severity = models.CharField(max_length=50, choices=SEVERITY_LEVELS, null=True, blank=True)
    notify_within = models.TimeField(default="02:00:0", null=True, blank=True)
    
    class Meta:
        db_table = "piloo_client_use_cases"
        indexes = [
            models.Index(fields=["severity"]),
        ]
            
    def __str__(self):
        return f"{self.client.name}-{self.usecase.type}"


class Alert(models.Model):
    """Security alerts and incidents"""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("resolved", "Resolved"),
        ("dismissed", "Dismissed"),
        ("investigating", "Under Investigation"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usecase = models.ForeignKey(ClientUseCase, on_delete=models.Case, related_name='client_alerts')
    label = models.CharField(max_length=150, null=True, blank=True)
    camera = models.ForeignKey(
        Camera, on_delete=models.CASCADE, related_name="camera_alerts"
    )
    timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    chunk_url = models.URLField(max_length=500, null=True, blank=True)
    frame_url = models.URLField(max_length=500, null=True, blank=True)
    confidence_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    metadata = models.JSONField(null=True, blank=True)  # Additional AI detection data
    resolved_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_alerts",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    owner = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="client_alerts", null=True, blank=True
    )
    notification_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "piloo_alerts"
        ordering = ["-timestamp"]
        unique_together = ('camera', 'label', 'timestamp')
        indexes = [
            # models.Index(fields=["type__type", "type__severity"]),
            models.Index(fields=["camera"]),
            models.Index(fields=["label"]),
            models.Index(fields=["timestamp"]),
            models.Index(fields=["status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['camera', 'label', 'timestamp'],
                name='unique_camera_label_timestamp')
        ]
        

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)

        # if is_new or self.status == "active":
        #     broadcast_dashboard_update(str(self.owner.id))

    def __str__(self):
        return f"{self.usecase.usecase.type} - {self.camera.name} ({self.timestamp})"


class DailyAlertsCount(models.Model):
    pass



class Report(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='client_reports')
    report = models.FileField(upload_to='layout/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "piloo_reports"


class Recording(models.Model):
    """Video recordings management"""

    QUALITY_CHOICES = [
        ("480p", "480p"),
        ("720p", "720p"),
        ("1080p", "1080p"),
        ("4K", "4K"),
    ]

    camera = models.ForeignKey(
        Camera, on_delete=models.CASCADE, related_name="recordings"
    )
    filename = models.CharField(max_length=100, null=True, blank=True)
    file_path = models.CharField(max_length=200, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration = models.DurationField()
    file_size = models.BigIntegerField(
        help_text="File size in bytes", null=True, blank=True
    )
    quality = models.CharField(max_length=10, choices=QUALITY_CHOICES, default="480p")
    has_motion = models.BooleanField(default=False)
    has_audio = models.BooleanField(default=False)
    thumbnail_path = models.CharField(max_length=500, null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    cloud_url = models.CharField(max_length=200, null=True, blank=True)
    checksum = models.CharField(max_length=64, null=True, blank=True)  # SHA-256 hash
    metadata = models.JSONField(null=True, blank=True)
    owner = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="recordings",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "piloo_recordings"
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["start_time", "end_time"]),
            models.Index(fields=["camera", "start_time"]),
            models.Index(fields=["has_motion"]),
        ]

    def __str__(self):
        return f"{self.camera.name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        self.cloud_url = os.path.join(settings.CDN_DOMAIN, self.file_path)
        super().save(*args, **kwargs)

    @property
    def duration_seconds(self):
        return self.duration.total_seconds()


class Employee(models.Model):
    """Employee monitoring and attendance tracking"""

    STATUS_CHOICES = [
        ("present", "Present"),
        ("absent", "Absent"),
        ("late", "Late"),
        ("on_break", "On Break"),
        ("checked_out", "Checked Out"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="absent")
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    last_seen_camera = models.ForeignKey(
        Camera, on_delete=models.SET_NULL, null=True, blank=True
    )
    date = models.DateField(default=timezone.now)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    face_encoding = models.JSONField(null=True, blank=True)  # For face recognition
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="employees",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "piloo_employees"
        ordering = ["name"]
        unique_together = ["employee_id", "date", "owner"]

    def __str__(self):
        return f"{self.name} ({self.employee_id}) - {self.date}"


class ClientSettings(models.Model):
    """System-wide configuration settings"""

    company = models.OneToOneField(
        Client, on_delete=models.CASCADE, related_name="client_settings"
    )
    alerts_intrusion = models.BooleanField(default=True)
    alerts_motion = models.BooleanField(default=True)
    alerts_unauthorized = models.BooleanField(default=True)
    recording_enabled = models.BooleanField(default=True)
    additional_recordings_storage = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(365)])
    additional_cameras = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(500)])
    recording_quality = models.CharField(max_length=10)
    retention_days = models.IntegerField(default=30, validators=[MinValueValidator(1)])
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    wa_notifications = models.BooleanField(default=False)
    ai_detection_enabled = models.BooleanField(default=True)
    face_recognition_enabled = models.BooleanField(default=False)
    timezone = models.CharField(max_length=50, default="UTC")
    language = models.CharField(max_length=10, default="en")
    theme = models.CharField(
        max_length=10, choices=[("light", "Light"), ("dark", "Dark")], default="light"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "piloo_client_settings"

    def __str__(self):
        return f"Settings for {self.company.name}"
    


class SystemSettings(models.Model):
    """System-wide configuration settings"""

    user = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE, related_name="system_settings"
    )
    alerts_intrusion = models.BooleanField(default=True)
    alerts_motion = models.BooleanField(default=True)
    alerts_unauthorized = models.BooleanField(default=True)
    recording_enabled = models.BooleanField(default=True)
    recording_quality = models.CharField(max_length=10, default="1080p")
    retention_days = models.IntegerField(default=30, validators=[MinValueValidator(1)])
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    ai_detection_enabled = models.BooleanField(default=True)
    face_recognition_enabled = models.BooleanField(default=False)
    cloud_backup_enabled = models.BooleanField(default=False)
    timezone = models.CharField(max_length=50, default="UTC")
    language = models.CharField(max_length=10, default="en")
    theme = models.CharField(
        max_length=10, choices=[("light", "Light"), ("dark", "Dark")], default="light"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "piloo_system_settings"

    def __str__(self):
        return f"Settings for {self.user.username}"


class SubscriptionPlan(models.Model):
    """Available subscription plans"""

    name = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cameras = models.IntegerField()
    features = models.JSONField(default=list)
    storage_gb = models.IntegerField(default=100)
    subscription_days = models.IntegerField(default=30)
    retention_days = models.IntegerField(default=30)
    ai_features = models.BooleanField(default=False)
    cloud_backup = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    stripe_price_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "piloo_subscription_plans"
        ordering = ["price"]

    def __str__(self):
        return f"{self.name} - ${self.price}/month"


class DemoRequest(models.Model):
    """Demo requests from potential customers"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("contacted", "Contacted"),
        ("scheduled", "Scheduled"),
        ("completed", "Completed"),
        ("declined", "Declined"),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    company = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    assigned_to = models.ForeignKey(
        UserProfile, on_delete=models.SET_NULL, null=True, blank=True
    )
    demo_scheduled_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "piloo_demo_requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.company}"


class SearchQuery(models.Model):
    """AI search queries and results tracking"""
    QUERY_ORIGIN = (('webapp', 'WebApp'),
                    ('whatsapp', 'WhatsApp'))
    user = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="search_queries"
    )
    query = models.TextField()
    filters = models.JSONField(null=True, blank=True)
    results_count = models.IntegerField(default=0)
    execution_time = models.DecimalField(
        max_digits=8, decimal_places=3, null=True, blank=True
    )  # in seconds
    cameras_searched = models.ManyToManyField(Camera, blank=True)
    time_range_start = models.DateTimeField(null=True, blank=True)
    time_range_end = models.DateTimeField(null=True, blank=True)
    origin = models.CharField(max_length=50, choices=QUERY_ORIGIN, default='webapp')
    results_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "piloo_search_queries"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username}: {self.query[:50]}..."


class OnboardingStep(models.Model):
    """Onboarding tutorial steps"""

    CATEGORIES = [
        ("getting_started", "Getting Started"),
        ("monitoring", "Monitoring"),
        ("security", "Security"),
        ("ai_features", "AI Features"),
        ("management", "Management"),
    ]

    step_number = models.IntegerField(unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    target_page = models.CharField(max_length=100)
    target_element = models.CharField(max_length=100, null=True, blank=True)
    instructions = models.TextField()
    points = models.IntegerField(default=10)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    estimated_time = models.IntegerField(
        default=5, help_text="Estimated time in minutes"
    )
    is_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    icon = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "piloo_onboarding_steps"
        ordering = ["step_number"]

    def __str__(self):
        return f"Step {self.step_number}: {self.title}"


class UserAchievement(models.Model):
    """Gamification achievements"""

    CATEGORIES = [
        ("onboarding", "Onboarding"),
        ("monitoring", "Monitoring"),
        ("security", "Security"),
        ("ai_usage", "AI Usage"),
        ("management", "Management"),
        ("milestone", "Milestone"),
    ]

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50)
    points = models.IntegerField(default=10)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    condition = models.JSONField(help_text="Condition for earning this achievement")
    is_active = models.BooleanField(default=True)
    rarity = models.CharField(
        max_length=10,
        choices=[
            ("common", "Common"),
            ("rare", "Rare"),
            ("epic", "Epic"),
            ("legendary", "Legendary"),
        ],
        default="common",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "piloo_achievements"
        ordering = ["category", "points"]

    def __str__(self):
        return f"{self.name} ({self.points} points)"


class OnboardingProgress(models.Model):
    """User onboarding progress and gamification tracking"""

    user = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE, related_name="progress"
    )
    current_step = models.IntegerField(default=1)
    completed_steps = models.JSONField(default=list)
    total_points = models.IntegerField(default=0)
    achievements = models.ManyToManyField(UserAchievement, blank=True)
    tutorial_completed = models.BooleanField(default=False)
    last_active_step = models.CharField(max_length=50, null=True, blank=True)
    onboarding_started = models.DateTimeField(null=True, blank=True)
    onboarding_completed = models.DateTimeField(null=True, blank=True)
    level = models.IntegerField(default=1)
    experience_points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "piloo_user_progress"

    def __str__(self):
        return f"{self.user.username} - Level {self.level} ({self.total_points} points)"

class TempNotification(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    phone = models.CharField(max_length=16, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)


class PDFReportNotification:
    pass

class Notification(models.Model):
    """System notifications for users"""

    NOTIFICATION_TYPES = [
        ("alert", "Security Alert"),
        ("system", "System Notification"),
        ("employee", "Employee Update"),
        ("camera", "Camera Status"),
        ("achievement", "Achievement Earned"),
        ("subscription", "Subscription Update"),
        ("email", "Email"),
        ("whatsapp", "WhatsApp"),
    ]

    PRIORITY_LEVELS = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="notifications_to_user",
        null=True,
        blank=True,
    )
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(
        max_length=10, choices=PRIORITY_LEVELS, default="medium"
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    action_url = models.URLField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    next_cycle = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "piloo_notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["type", "priority"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.company.name}"


class ActivityLog(models.Model):
    """User activity and system event logging"""

    ACTION_TYPES = [
        ("login", "User Login"),
        ("logout", "User Logout"),
        ("camera_add", "Camera Added"),
        ("camera_edit", "Camera Modified"),
        ("camera_delete", "Camera Deleted"),
        ("alert_acknowledge", "Alert Acknowledged"),
        ("alert_resolve", "Alert Resolved"),
        ("recording_view", "Recording Viewed"),
        ("recording_download", "Recording Downloaded"),
        ("settings_change", "Settings Modified"),
        ("search_query", "AI Search Performed"),
        ("employee_add", "Employee Added"),
        ("zone_create", "Zone Created"),
        ("subscription_change", "Subscription Modified"),
    ]

    user = models.ForeignKey(
        UserProfile, on_delete=models.SET_NULL, null=True, blank=True
    )
    action = models.CharField(max_length=30, choices=ACTION_TYPES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "piloo_activity_logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["action", "timestamp"]),
        ]

    def __str__(self):
        user_name = self.user.username if self.user else "System"
        return f"{user_name} - {self.get_action_display()} ({self.timestamp})"


# Signal handlers for automatic model updates
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver


# @receiver(post_save, sender=UserProfile)
# def create_user_profile(sender, instance, created, **kwargs):
#     """Create related models when a new user is created"""
#     if created:
#         OnboardingProgress.objects.create(
#             user=instance, onboarding_started=timezone.now()
#         )
#         MenuPermission.objects.create(user=instance)
        # SystemSettings.objects.create(user=instance)      
        

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


# @receiver(post_save, sender=Alert)
# def create_alert_notification(sender, instance, created, **kwargs):
#     """Create notification when new alert is generated"""
#     if created and instance.type.severity in ["high", "critical"]:
#         Notification.objects.create(
#             company=instance.owner,
#             type="alert",
#             priority=instance.severity,
#             title=f"New {instance.get_severity_display()} Alert",
#             message=f"{instance.get_type_display()} detected at {instance.camera.location}",
#             data={"alert_id": instance.id, "camera_id": instance.camera.id},
#         )


# @receiver(post_save, sender=DemoRequest)
# def demo_request_user(sender, instance, created, **kwargs):
#     """Create related model when a new Demo Request Received is created"""
    # if created:
    #     UserProfile.objects.create(
    #         email=instance.email,
    #         phone=instance.phone if instance.phone else None,
    #         role="demo",
    #         is_active=True,
    #         is_verified=True,
    #     )          
        
        
class ClientPayment(models.Model):
    """Client payment records for subscription management"""
    PAYMENT_STATUS_CHOICES = [
        ("created", "Created"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="payments")
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    
    razorpay_order_id = models.CharField(max_length=100)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="created")
    
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "client_payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.client.name} | ₹{self.amount} | {self.status}"
