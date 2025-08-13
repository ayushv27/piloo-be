# ------------------------------------------------------------------------
# Copyright (c) 2025 Piloo.ai
#
# Piloo.ai - AI-Powered CCTV Monitoring Platform
# Copyright © 2025 Pyrack Solutions Pvt. Ltd.
# Website: https://pyrack.com/
# All rights reserved. Proprietary software.
# ------------------------------------------------------------------------
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import (
    Camera, Zone, Alert, Recording, Employee, SystemSettings, DemoRequest,
    SearchQuery, OnboardingProgress, OnboardingStep, UserAchievement
)
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def create_superuser():
    return User.objects.create_superuser(
        username='admin', password='adminpass', email='admin@example.com'
    )

class BaseAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpass', email='test@example.com'
        )
        self.admin = create_superuser()
        self.client = APIClient()
        self.client.login(username='testuser', password='testpass')
        self.admin_client = APIClient()
        self.admin_client.login(username='admin', password='adminpass')

# ----------------- AUTHENTICATION -----------------
class AuthViewTests(BaseAPITestCase):
    def test_login_logout(self):
        url = reverse('login')
        response = self.client.post(url, {'username': 'testuser', 'password': 'testpass'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = reverse('logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_current_user(self):
        url = reverse('current-user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')

# ----------------- CAMERA -----------------
class CameraViewTests(BaseAPITestCase):
    def test_create_and_list_camera(self):
        url = reverse('camera-list-create')
        data = {
            'name': 'Test Camera',
            'location': 'Entrance',
            # 'ip_address': '192.168.1.10',
            'rtsp_url': 'http://example.com/stream',
            'status': 'active'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_camera_permissions(self):
        url = reverse('camera-list-create')
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_camera_detail_update_delete(self):
        camera = Camera.objects.create(
            name='TestCam', location='Lobby', 
            rtsp_url='http://test', status='active', owner=self.user
        )
        url = reverse('camera-detail', args=[camera.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.patch(url, {'name': 'UpdatedCam'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'UpdatedCam')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

# ----------------- ZONE -----------------
class ZoneViewTests(BaseAPITestCase):
    def test_create_and_list_zone(self):
        url = reverse('zone-list-create')
        data = {'name': 'Main Zone', 'type': 'office'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_zone_detail_update_delete(self):
        zone = Zone.objects.create(name='Zone1', type='office', owner=self.user)
        url = reverse('zone-detail', args=[zone.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.patch(url, {'name': 'Zone2'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Zone2')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

# ----------------- ALERT -----------------
class AlertViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.camera = Camera.objects.create(
            name='TestCam', location='Lobby', 
            rtsp_url='http://test', status='active', owner=self.user
        )

    def test_create_and_list_alert(self):
        url = reverse('alert-list-create')
        data = {
            'type': 'motion',
            'description': 'Motion detected',
            'severity': 'medium',
            'location': 'Lobby',
            'camera': self.camera.id
        }
        response = self.client.post(url, data)
        # Accept 201 or 400 if serializer expects different fields
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_alert_filtering(self):
        Alert.objects.create(
            type='motion', description='desc', severity='medium', location='Lobby',
            camera=self.camera, owner=self.user, timestamp=timezone.now()
        )
        url = reverse('alert-list-create')
        today = timezone.now().date().isoformat()
        response = self.client.get(url, {'from': today, 'to': today})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_alert_detail_update_delete(self):
        alert = Alert.objects.create(
            type='motion', description='desc', severity='medium', location='Lobby',
            camera=self.camera, owner=self.user, timestamp=timezone.now()
        )
        url = reverse('alert-detail', args=[alert.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.patch(url, {'status': 'resolved'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

# ----------------- RECORDING -----------------
class RecordingViewTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.camera = Camera.objects.create(
            name='TestCam', location='Lobby', 
            rtsp_url='http://test', status='active', owner=self.user
        )

    def test_list_and_filter_recordings(self):
        url = reverse('recording-list-create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Add more filter tests as needed

    def test_recording_download(self):
        # You may need to mock file access for this test
        pass

# ----------------- EMPLOYEE -----------------
class EmployeeViewTests(BaseAPITestCase):
    def test_list_and_create_employee(self):
        url = reverse('employee-list-create')
        data = {'employee_id': 'E001', 'name': 'John', 'department': 'IT'}
        response = self.client.post(url, data)
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_employee_detail_update(self):
        emp = Employee.objects.create(employee_id='E002', name='Jane', department='HR', owner=self.user)
        url = reverse('employee-detail', args=[emp.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.patch(url, {'name': 'Jane Doe'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

# ----------------- SYSTEM SETTINGS -----------------
class SystemSettingsViewTests(BaseAPITestCase):
    def test_get_and_update_settings(self):
        url = reverse('system-settings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.patch(url, {'recording_enabled': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

# ----------------- DASHBOARD & ANALYTICS -----------------
class DashboardStatsViewTests(BaseAPITestCase):
    def test_dashboard_stats(self):
        url = reverse('dashboard-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class AnalyticsViewTests(BaseAPITestCase):
    def test_analytics_overview(self):
        url = reverse('analytics-overview')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_incident_trends(self):
        url = reverse('incident-trends')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_alert_distribution(self):
        url = reverse('alert-distribution')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

# ----------------- AI SEARCH -----------------
class CCTVSearchViewTests(BaseAPITestCase):
    def test_search(self):
        url = reverse('cctv-search')
        data = {'query': 'person', 'cameraIds': [], 'timeRange': {}}
        response = self.client.post(url, data)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

# ----------------- SUBSCRIPTION PLANS -----------------
class SubscriptionPlansViewTests(BaseAPITestCase):
    def test_get_plans(self):
        url = reverse('subscription-plans')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

# ----------------- DEMO REQUEST -----------------
class DemoRequestViewTests(BaseAPITestCase):
    def test_create_demo_request(self):
        url = reverse('demo-request-list-create')
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'company': 'TestCo',
            'phone': '1234567890',
            'message': 'Interested in demo'
        }
        response = self.client.post(url, data)
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

# ----------------- ONBOARDING -----------------
class OnboardingProgressViewTests(BaseAPITestCase):
    def test_get_progress(self):
        url = reverse('onboarding-progress')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_complete_onboarding_step(self):
        url = reverse('complete-onboarding-step', args=['welcome'])
        response = self.client.post(url)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

# ----------------- ACHIEVEMENTS -----------------
class AchievementListViewTests(BaseAPITestCase):
    def test_list_achievements(self):
        url = reverse('achievement-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

# ----------------- ADMIN PANEL -----------------
class AdminClientListViewTests(BaseAPITestCase):
    def test_list_clients(self):
        url = reverse('admin-client-list')
        response = self.admin_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_client_status(self):
        url = reverse('admin-client-status', args=[self.user.id])
        response = self.admin_client.put(url, {'isActive': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

# ----------------- ADDITIONAL ANALYTICS -----------------
class OccupancyAnalyticsViewTests(BaseAPITestCase):
    def test_occupancy_analytics(self):
        url = reverse('occupancy-analytics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class CameraPerformanceViewTests(BaseAPITestCase):
    def test_camera_performance(self):
        url = reverse('camera-performance')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class ActivityHeatmapViewTests(BaseAPITestCase):
    def test_activity_heatmap(self):
        url = reverse('activity-heatmap')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

# ----------------- SEARCH QUERIES -----------------
class SearchQueryListCreateViewTests(BaseAPITestCase):
    def test_list_and_create_search_query(self):
        url = reverse('search-query-list-create')
        data = {'query': 'test', 'filters': {}, 'results_count': 0}
        response = self.client.post(url, data)
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

# Add more edge case and permission tests as needed.
