import pytest
import json
from django.urls import reverse
from rest_framework import status
from core.models import * 
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
# import datetime
from datetime import timedelta
from django.utils import timezone


@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def subscription_plan(db):
    return SubscriptionPlan.objects.create(
        name = 'Test Plan',
        price = 1000,
        cameras = 10,
        features = ['feature1', 'feature2'],
        storage_gb = 100,
        subscription_days = 30,       
    )

@pytest.fixture
def client(db, subscription_plan):
    return Client.objects.create(
        name='Test Client',
        subscription_plan=subscription_plan,
        subscription_status='active'
        )

@pytest.fixture
def admin_user(db,client):
    return UserProfile.objects.create_user(
        email='admin@test.com',
        password='testpass123',
        role='admin',
        is_active=True,
        # name='Test Admin',
        phone='1234567890',
        is_superuser=True,
        is_staff=True,
        company = client
    )

@pytest.fixture
def authenticated_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def zone(db, client, admin_user):
    return Zone.objects.create(
        name='Test Zone',
        type='restricted',
        description='Test Zone Description',
        is_active=True,
        owner=client,
        created_by=admin_user
    )

@pytest.fixture
def camera(db, client, zone):
    return Camera.objects.create(
        name='Test Camera',
        location='Test location',
        # ip_address='192.168.1.10',
        rtsp_url= "rtsp://192.168.1.10:554/live.sdp",
        status='active',
        recording_enabled=True,
        retention_days=1,
        quality='1080p',
        has_audio=False,
        pan_tilt_zoom=False,
        night_vision=False,
        outdoor_rated=False,
        uptime_percentage=0.0,
        owner=client,
        assigned_zone=zone
    )


@pytest.fixture
def ml_model(db):
    return MLModel.objects.create(name = 'test_model')  


@pytest.fixture
def alert_type_master(db, ml_model):
    return AlertTypeMaster.objects.create(
        ml_model = ml_model,
        type = 'test_type',
        name = 'Test Alert Type',
        severity = 'high'
    )  


@pytest.fixture
def alert(db, camera, admin_user, client, alert_type_master):
    now = timezone.now()
    return Alert.objects.create(
        type=alert_type_master,
        label='Test Alert',
        camera=camera,
        resolved_by=admin_user,
        owner=client,
        timestamp=now,
    )


@pytest.fixture
def recording(db, camera, client):
    start_time = timezone.now() - timedelta(minutes=30)
    end_time = timezone.now()
    duration = end_time - start_time
    return Recording.objects.create(
        camera= camera,
        filename='test_recording.mp4',
        file_path='path/to/test_recording.mp4',
        quality='1080p',
        start_time=start_time,
        end_time=end_time,
        duration=duration,
        file_size=10485760,
        has_motion=False,
        has_audio=False,
        is_archived=False,
        owner=client,
    )    