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
from analytics.views import GeneratePDFReportAPI

# API URL patterns
#dash
urlpatterns = [     
    # Dashboard statistics
    # path('api/stats/', views.dashboard_stats, name='dashboard-stats'),
    # path('v1/dash-stats-sse/', views.dashboard_stats_sse, name='dashboard-SSE-stats'),
    path('v1/camera-status/', views.sse_camera_status_updates, name="sse for camera status update"),
    # path('v1/sse_test/', views.sse_test, name='test'),
    # Analytics endpoints
    path('v1/analytics/', views.analytics_overview, name='analytics-overview'),
    path('v1/analytics/incident-trends/', views.incident_trends, name='incident-trends'),
    path('v1/analytics/alert-distribution/', views.alert_distribution, name='alert-distribution'),
    path('v1/analytics/occupancy/', views.occupancy_analytics, name='occupancy-analytics'),
    path('api/analytics/camera-performance/', views.camera_performance, name='camera-performance'),
    path('v1/analytics/activity-heatmap/', views.activity_heatmap, name='activity-heatmap'),
    path('v1/getreport/', views.GenerateReportView.as_view(), name='daily pdf report'),
    path('v1/send-notification/', views.send_criticle_notification, name='send WhatsApp notifications'),
    path('v2/send-notification/', views.send_notification, name='send WhatsApp notifications'),
    path('generate-report/<uuid:client_id>/', GeneratePDFReportAPI.as_view(), name='generate_pdf_report'), # testing purpose
    path('v1/analytics/eventtype-count/', views.ClientEventCountPerDayView.as_view(), name='eventtype-count'),
    path("v1/analytics/alert-count/", views.DayWiseAlertCountView.as_view(), name="day-wise-alert-count"),
    path('get-report/', views.get_report, name='generate_pdf_report'),
    path('test-emails/', views.SendTestAlertView.as_view(), name='client-alerts'), #testing purpose
]

