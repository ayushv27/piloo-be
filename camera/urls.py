# ------------------------------------------------------------------------
# Copyright (c) 2025 Piloo.ai
#
# Piloo.ai - AI-Powered CCTV Monitoring Platform
# Copyright © 2025 Pyrack Solutions Pvt. Ltd.
# Website: https://pyrack.com/
# All rights reserved. Proprietary software.
# ------------------------------------------------------------------------
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API URL patterns
urlpatterns = [

    # Camera management
    path('v1/cameras/', views.CameraListCreateView.as_view(), name='camera-list-create'),
    path('v1/cameras/<str:pk>/', views.CameraDetailView.as_view(), name='camera-detail'),
    path('v1/camerasname/', views.CameraNameListView.as_view(), name='camera-name-list'),
    path('v1/activecameras/', views.CameraListView.as_view(), name='camera-list'),
    
    # Zone management
    path('v1/zones/', views.ZoneListCreateView.as_view(), name='zone-list-create'),
    path('v1/zonenames/', views.ZoneNameListView.as_view(), name='zone names list'),
    path('v1/zones/<str:pk>/', views.ZoneDetailView.as_view(), name='zone-detail'),
    
    # Alert management
    path('v1/alerts/', views.AlertListCreateView.as_view(), name='alert-list-create'),
    path('v1/alerts/<str:pk>/', views.AlertDetailView.as_view(), name='alert-detail'),
    # path('v1/alerts/eventtype/', views.AlertEventTypeListView.as_view(), name='alert-list-eventtype'),
    path('v1/alerts/eventtype/list/', views.AlertEventTypeListView.as_view(), name='alert-eventtype-list'),    
    
    # Recording management
    path('v1/recordings/', views.RecordingListCreateView.as_view(), name='recording-list-create'),
    path('v1/recordings/<str:pk>/', views.RecordingDetailView.as_view(), name='recording-detail'),
    path('v1/recordings/download/<str:pk>/', views.RecordingDownloadView.as_view(), name='recording-download'),   
    path('v1/s3bulkrecordings/', views.BulkRecordingLoadAndListView.as_view(), name='bulk-recording-load-list'), 
    path('v1/recording-list/', views.RecordingListView.as_view(), name='recording-list'),   

]

# WebSocket URL patterns (if using Django Channels)
# websocket_urlpatterns = [
#     path('ws/', views.WebSocketConsumer.as_asgi()),  # This would be defined in consumers.py
# ]