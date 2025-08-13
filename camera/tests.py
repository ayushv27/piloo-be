from django.test import TestCase

import pytest
import tempfile
import json
import os
from django.urls import reverse
from rest_framework import status
from core.models import * 
from rest_framework.test import APIClient
from Tests.tests_models import *

@pytest.mark.django_db
class TestCameraAPI:
    def test_camera_list_view(self, authenticated_client, camera):
        """Test the camera list view to ensure it returns a list of cameras."""
        url = '/cam/v1/cameras/'

        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK

        assert isinstance(response.data, list)
        assert len(response.data) > 0
        assert response.data[0]["name"] == camera.name

    def test_camera_create_admin_view(self, authenticated_client, client, camera):  
        """Test the camera create view to ensure it creates a new camera using admin user."""
        url = '/cam/v1/cameras/'
        
        data = {
            "name": "Admin Camera",
            "location": "HQ",
            "ip_address": "10.0.0.1",
            "rtsp_url": "rtsp://10.0.0.1/stream",
            "status": "active",
            "owner": client.id,
            "retention_days": 3,
            "recording_enabled": True,
        }

        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED

        assert response.data["name"] == data["name"]
        assert response.data["location"] == data["location"]
        assert Camera.objects.filter(name="Admin Camera").exists()

    def test_camera_create_view(self, api_client, client, django_user_model):
        """Test the camera create view to ensure it creates a new camera using non-admin user."""
        
        test_user = django_user_model.objects.create_user(
                
                email='testuser@example.com',
                password='testpass123',
                role='manager',
                company=client
            )
        
        api_client.force_authenticate(user=test_user)
        url = '/cam/v1/cameras/'

        data = {
            "name": "Client Camera",
            "location": "Site A",
            "ip_address": "10.0.0.2",
            "rtsp_url": "rtsp://10.0.0.2/stream",
            "status": "active",
            "retention_days": 5,
            "recording_enabled": False,
            "owner": client.id,
        }

        response = api_client.post(url, data, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED

        camera = Camera.objects.get(name="Client Camera")
        assert camera.owner == client 

    def test_camera_detail_retrieve_view(self, authenticated_client, camera):

        """Test the camera detail view to ensure it retrieves a specific camera's details."""

        url = f'/cam/v1/cameras/{camera.id}/' 
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == camera.name
        assert response.data["location"] == camera.location

    def test_camera_detail_update_view(self, authenticated_client, camera):
        
        """Test the camera detail view to ensure it updates a specific camera's details."""

        url = f'/cam/v1/cameras/{camera.id}/'

        data = {
            "name": "Updated Camera",
            "location": "New Location",           
        }

        response = authenticated_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == data["name"]
        assert response.data["location"] == data["location"]

    def test_camera_detail_delete_view(self, authenticated_client, camera):

        """Test the camera detail view to ensure it deletes a specific camera."""

        url = f'/cam/v1/cameras/{camera.id}/'

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Camera.objects.filter(id=camera.id).exists()    

    def test_zone_list_view(self, authenticated_client, zone):

        """Test the zone list view to ensure it returns a list of zones."""

        url = '/cam/v1/zones/'

        response = authenticated_client.get(url)
        print("Response data:", response.data)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) > 0
        assert response.data[0]["name"] == zone.name

    def test_zone_create_admin_view(self, authenticated_client, client):

        """Test the zone create view to ensure it creates a new zone using admin role."""

        url = '/cam/v1/zones/'

        data = {
            "name": "New Zone",
            "description": "Zone for testing",
            "type": "restricted",
     
        }

        response = authenticated_client.post(url, data, format='json')
       
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == data["name"]
        assert Zone.objects.filter(name="New Zone").exists()     

    def test_zone_create_view(self, authenticated_client, client):
        """Test the zone create view to ensure it creates a new zone using non-admin role."""

        url = '/cam/v1/zones/'

        data = {
            "name": "Client Zone",
            "description": "Zone for client",
            "type": "restricted",
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == data["name"]
        assert Zone.objects.filter(name="Client Zone").exists()  

    def test_zone_detail_retrieve_view(self, authenticated_client, zone):

        """Test the zone detail view to ensure it retrieves a specific zone's details."""

        url = f'/cam/v1/zones/{zone.id}/'

        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == zone.name
        assert response.data["description"] == zone.description

    def test_zone_detail_update_view(self, authenticated_client, zone):

        """Test the zone detail view to ensure it updates a specific zone's details."""

        url = f'/cam/v1/zones/{zone.id}/'

        data = {
            "name": "Updated Zone",
            "description": "Updated description",
        }

        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == data["name"]
        assert response.data["description"] == data["description"]    

    def test_zone_detail_delete_view(self, authenticated_client, zone):

        """Test the zone detail view to ensure it deletes a specific zone."""

        url = f'/cam/v1/zones/{zone.id}/'

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Zone.objects.filter(id=zone.id).exists()    

    def test_alert_list_view(self, authenticated_client, alert, admin_user):

        """Test the alert list view to ensure it returns a list of alerts."""

        url = '/cam/v1/alerts/'
        authenticated_client.force_authenticate(user=admin_user)

        params = {
            "eventType": str(alert.type.id),
            "cameraId": alert.camera.id,
            "zone_id": str(alert.camera.assigned_zone.id),
            "search": alert.type.type,            
        }

        response = authenticated_client.get(url, params)
        
        assert response.status_code == status.HTTP_200_OK
        print("Response data:", response.data)        
        
        results = response.data

        assert isinstance(results, list)
        assert any(str(a["id"]) == str(alert.id) for a in results)

    def test_alert_create_view(self, authenticated_client, client, camera, alert_type_master, admin_user):

        """Test the alert create view to ensure it creates a new alert."""

        url = '/cam/v1/alerts/'

        data = {            
            "type": alert_type_master.id, 
            "label": "Test Alert",
            "camera": camera.id,           
            "status": "active",
            "video_url": "http://example.com/video.mp4",
            "owner": client.id,
            # "resolved_by": admin_user.id,
        }

        response = authenticated_client.post(url, data, format='json')
                
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["label"] == data["label"]
        assert Alert.objects.filter(label="Test Alert").exists()

    def test_alert_detail_retrieve_view(self, authenticated_client, alert):

        """Test the alert detail view to ensure it retrieves a specific alert's details."""

        url = f'/cam/v1/alerts/{alert.id}/'

        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["label"] == alert.label
        assert response.data["type"] == alert.type.id

    def test_alert_detail_update_view(self, authenticated_client, alert):

        """Test the alert detail view to ensure it updates a specific alert's details."""

        url = f'/cam/v1/alerts/{alert.id}/'

        data = {
            "label": "Updated label",            
        }

        response = authenticated_client.patch(url, data, format='json')
        print("Response data:", response.data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["label"] == "Updated label"        

    def test_alert_detail_delete_view(self, authenticated_client, alert):

        """Test the alert detail view to ensure it deletes a specific alert."""

        url = f'/cam/v1/alerts/{alert.id}/'

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Alert.objects.filter(id=alert.id).exists() 

    def test_recording_list_view(self, authenticated_client, recording):

        """Test the recording list view to ensure it returns a list of recordings."""

        url = '/cam/v1/recordings/'

        params = {
            "cameraId": recording.camera.id,
            "startDate": recording.start_time.isoformat(),
            "endDate": recording.end_time.isoformat(),
            "quality": recording.quality,
            "hasMotion": str(recording.has_motion).lower(),
        }

        response = authenticated_client.get(url, params)

        assert response.status_code == status.HTTP_200_OK

        data_list = response.data["results"] if "results" in response.data else response.data

        assert isinstance(data_list, list)
        assert any(r["id"] == recording.id for r in data_list)      

    def test_recording_create_view(self, authenticated_client, camera, client):

        """Test the recording create view to ensure it creates a new recording."""

        url = '/cam/v1/recordings/'

        data = {
            "cameraId": camera.id,
            "fileName": "test_recording.mp4",
            "filePath": "/path/to/test_recording.mp4",
            "startTime": "2025-01-01T00:00:00Z",
            "endTime": "2025-01-01T01:00:00Z",
            "duration": "PT1H", 
            "fileSize": 1024000,
            "quality": "1080p",
            "hasMotion": True,
            "hasAudio": False,
            "thumbnailPath": "/path/to/thumbnail.jpg",
           
        }

        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["fileName"] == data["fileName"]
        assert Recording.objects.filter(filename="test_recording.mp4").exists()

    def test_recording_detail_retrieve_view(self, authenticated_client, recording):

        """Test the recording detail view to ensure it retrieves a specific recording's details."""

        url = f'/cam/v1/recordings/{recording.id}/'

        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["fileName"] == recording.filename
        assert response.data["quality"] == recording.quality

    def test_recording_detail_delete_view(self, authenticated_client, recording, client, camera):

        """Test the recording detail view to ensure it deletes a specific recording."""

        url = f'/cam/v1/recordings/{recording.id}/'

        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Recording.objects.filter(id=recording.id).exists()

    def test_recording_download_view(self, authenticated_client, recording):

        """Test the recording download view to ensure it downloads a specific recording."""
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
            tmp_file.write(b"dummy video content")
            tmp_file_path = tmp_file.name

       
        recording.file_path = tmp_file_path
        recording.save()

        url = f"/cam/v1/recordings/download/{recording.id}/"
        response = authenticated_client.get(url)

        
        os.remove(tmp_file_path)

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "video/mp4"
        assert response["Content-Disposition"] == f'attachment; filename="{recording.filename}"'

        content = b''.join(response.streaming_content)
        assert b"dummy video content" in content   

         