# ------------------------------------------------------------------------
# Copyright (c) 2025 Piloo.ai
#
# Piloo.ai - AI-Powered CCTV Monitoring Platform
# Copyright © 2025 Pyrack Solutions Pvt. Ltd.
# Website: https://pyrack.com/
# All rights reserved. Proprietary software.
# ------------------------------------------------------------------------
from rest_framework import serializers

class StatsSerializer(serializers.Serializer):
    activeCameras = serializers.IntegerField()
    todayIncidents = serializers.IntegerField()
    currentAlerts = serializers.IntegerField()
    zoneCoverage = serializers.CharField()
    employeeStats = serializers.DictField()


class AnalyticsSerializer(serializers.Serializer):
    totalIncidents = serializers.IntegerField()
    todayIncidents = serializers.IntegerField()
    activeCameras = serializers.IntegerField()
    criticalAlerts = serializers.IntegerField()
    resolvedIncidents = serializers.IntegerField()
    avgResponseTime = serializers.IntegerField()


class IncidentTrendSerializer(serializers.Serializer):
    date = serializers.CharField()
    incidents = serializers.IntegerField()
    resolved = serializers.IntegerField()
    critical = serializers.IntegerField()
    high = serializers.IntegerField()
    medium = serializers.IntegerField()
    low = serializers.IntegerField()


class AlertDistributionSerializer(serializers.Serializer):
    name = serializers.CharField()
    value = serializers.IntegerField()
    percentage = serializers.FloatField()


class OccupancySerializer(serializers.Serializer):
    zone = serializers.CharField()
    occupancy = serializers.IntegerField()
    capacity = serializers.IntegerField()
    percentage = serializers.FloatField()


class CameraPerformanceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    uptime = serializers.FloatField()
    alerts = serializers.IntegerField()
    lastMaintenance = serializers.DateTimeField()
    status = serializers.CharField()


class ActivityHeatmapSerializer(serializers.Serializer):
    hour = serializers.CharField()
    monday = serializers.IntegerField()
    tuesday = serializers.IntegerField()
    wednesday = serializers.IntegerField()
    thursday = serializers.IntegerField()
    friday = serializers.IntegerField()
    saturday = serializers.IntegerField()
    sunday = serializers.IntegerField()


class StatusUpdateSerializer(serializers.Serializer):
    isActive = serializers.BooleanField()


class SubscriptionUpdateSerializer(serializers.Serializer):
    planName = serializers.CharField()


class EventCountPerDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    day = serializers.CharField()
    event_name = serializers.CharField()
    count = serializers.IntegerField()


class DayWiseAlertCountSerializer(serializers.Serializer):
    date = serializers.DateField()
    alert_count = serializers.IntegerField()