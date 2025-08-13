# ------------------------------------------------------------------------
# Copyright (c) 2025 Piloo.ai
#
# Piloo.ai - AI-Powered CCTV Monitoring Platform
# Copyright © 2025 Pyrack Solutions Pvt. Ltd.
# Website: https://pyrack.com/
# All rights reserved. Proprietary software.
# ------------------------------------------------------------------------
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.models import Permission
from core.models import (
    Client, Domain, AlertTypeMaster, ClientUseCase, UserProfile, Employee, 
    SystemSettings, DemoRequest, SearchQuery, OnboardingProgress,
    OnboardingStep, UserAchievement, MenuPermission, SubscriptionPlan
)
import re


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = '__all__'
        

class ClientSerializer(serializers.ModelSerializer):
    subscription_name = serializers.CharField(source='subscription_plan.name', read_only=True)
    client_cameras = serializers.SerializerMethodField()
    client_zones = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = '__all__'
        
    def get_client_cameras(self, obj):
        return obj.cameras.count()
    
    def get_client_zones(self, obj):
        return obj.zones.count()
        
        

class AlertTypeMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertTypeMaster
        fields = '__all__'
        
        

class ClientUseCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientUseCase
        fields = '__all__'        
        

class UserSerializer(serializers.ModelSerializer):
    subscriptionPlan = serializers.CharField(source='company.subscription_plan.name', read_only=True)
    # role = serializers.CharField(source='role', read_only=True)
    maxCameras = serializers.IntegerField(source='company.subscription_plan.cameras', read_only=True)
    isActive = serializers.BooleanField(source='is_active', read_only=True)
    lastLogin = serializers.DateTimeField(source='last_login', read_only=True)
    createdAt = serializers.DateTimeField(source='date_joined', read_only=True)
    company = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'phone', 'company', 'role', 
                  'isActive', 'lastLogin', 'createdAt', 'subscriptionPlan', 'maxCameras']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    company = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all(), required=False)

    
    class Meta:
        model = UserProfile
        # fields = ['email', 'phone', 'password', 'company', 'role']
        fields = '__all__'

    def create(self, validated_data):
        # user = UserProfile.objects.create_user(**validated_data)
        # return user
        password = validated_data.pop('password', None)
        
        username = validated_data.get('email') or validated_data.get('phone')
        validated_data['username'] = username

        user = UserProfile(**validated_data)

        if password:
            user.set_password(password)

        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    subscriptionPlan = serializers.CharField(source='company.subscription_plan.name', read_only=True)
    maxCameras = serializers.IntegerField(source='company.subscription_plan.cameras', read_only=True)
    stripe_customer_id = serializers.CharField(source='company.stripe_customer_id', read_only=True)
    stripe_subscription_id = serializers.IntegerField(source='company.stripe_subscription_id', read_only=True)
    subscription_ends_at = serializers.IntegerField(source='company.subscription_ends_at', read_only=True)
    menuPermissions = serializers.JSONField(source='menu_permissions', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'subscription_plan', 'max_cameras', 'stripe_customer_id',
                 'stripe_subscription_id', 'subscription_ends_at', 
                 'menuPermissions']


class AdminUserSerializer(serializers.ModelSerializer):
    # subscriptionPlan = serializers.CharField(source='userprofile.subscription_plan')
    # subscriptionStatus = serializers.CharField(source='userprofile.subscription_status', read_only=True)
    # maxCameras = serializers.IntegerField(source='userprofile.max_cameras')
    # stripeCustomerId = serializers.CharField(source='userprofile.stripe_customer_id', read_only=True)
    # stripeSubscriptionId = serializers.CharField(source='userprofile.stripe_subscription_id', read_only=True)
    # subscriptionEndsAt = serializers.DateTimeField(source='userprofile.subscription_ends_at', read_only=True)
    createdAt = serializers.DateTimeField(source='date_joined', read_only=True)
    lastLogin = serializers.DateTimeField(source='last_login', read_only=True)
    isActive = serializers.BooleanField(source='is_active')
    role = serializers.CharField(source='userprofile.role')
    menuPermissions = serializers.JSONField(source='userprofile.menu_permissions')
    
    class Meta:
        model = User
        model = UserProfile
        fields = ['id', 'username', 'email', 'role', 
                #   'subscriptionPlan', 
                #  'subscriptionStatus', 'maxCameras', 'stripeCustomerId', 
                #  'stripeSubscriptionId', 'subscriptionEndsAt', 
                 'createdAt',
                 'lastLogin', 'isActive', 'user_permissions']

    def update(self, instance, validated_data):
        profile_data = {}
        if 'userprofile' in validated_data:
            profile_data = validated_data.pop('userprofile')
        
        # Update User fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update UserProfile fields
        if profile_data:
            profile = instance.userprofile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance
    
class AdminClientSerializer(serializers.ModelSerializer):
    
    createdAt = serializers.DateTimeField(source='date_joined', read_only=True)
    lastLogin = serializers.DateTimeField(source='last_login', read_only=True)
    isActive = serializers.BooleanField(source='is_active')
    role = serializers.CharField()    
    user_permissions = serializers.SlugRelatedField(many=True,queryset=Permission.objects.all(),
                                                    slug_field='codename')           
        
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'role',             
                'createdAt', 'lastLogin', 'isActive', 'user_permissions']
        

class EmployeeSerializer(serializers.ModelSerializer):
    employeeId = serializers.CharField(source='employee_id')
    checkIn = serializers.DateTimeField(source='check_in')
    checkOut = serializers.DateTimeField(source='check_out')
    lastSeen = serializers.DateTimeField(source='last_seen')

    class Meta:
        model = Employee
        fields = ['id', 'name', 'employeeId', 'department', 'status', 
                 'checkIn', 'checkOut', 'lastSeen', 'date']


class SystemSettingsSerializer(serializers.ModelSerializer):
    alertsIntrusion = serializers.BooleanField(source='alerts_intrusion')
    alertsMotion = serializers.BooleanField(source='alerts_motion')
    alertsUnauthorized = serializers.BooleanField(source='alerts_unauthorized')
    recordingEnabled = serializers.BooleanField(source='recording_enabled')
    recordingQuality = serializers.CharField(source='recording_quality')
    retentionDays = serializers.IntegerField(source='retention_days')
    emailNotifications = serializers.BooleanField(source='email_notifications')
    smsNotifications = serializers.BooleanField(source='sms_notifications')

    class Meta:
        model = SystemSettings
        fields = ['id', 'alertsIntrusion', 'alertsMotion', 'alertsUnauthorized',
                 'recordingEnabled', 'recordingQuality', 'retentionDays',
                 'emailNotifications', 'smsNotifications']


class DemoRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemoRequest
        fields = ['id', 'name', 'email', 'company', 'phone', 'message', 'created_at']


class SearchQuerySerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source='user_id')

    class Meta:
        model = SearchQuery
        # fields = ['id', 'userId', 'query', 'filters', 'results', 'created_at']
        fields = ['id', 'userId', 'query', 'filters', 'created_at']


class CCTVSearchSerializer(serializers.Serializer):
    query = serializers.CharField()
    cameraIds = serializers.ListField(child=serializers.IntegerField(), required=False)
    timeRange = serializers.DictField(required=False)

    def validate_timeRange(self, value):
        if value:
            if 'start' not in value or 'end' not in value:
                raise serializers.ValidationError("timeRange must include 'start' and 'end'")
        return value


class CCTVSearchResultSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField()
    cameraId = serializers.IntegerField()
    cameraName = serializers.CharField()
    description = serializers.CharField()
    confidence = serializers.FloatField()
    videoUrl = serializers.CharField()
    thumbnailUrl = serializers.CharField()


class CCTVSearchResponseSerializer(serializers.Serializer):
    results = CCTVSearchResultSerializer(many=True)
    summary = serializers.CharField()
    totalResults = serializers.IntegerField()


class OnboardingStepSerializer(serializers.ModelSerializer):
    stepNumber = serializers.IntegerField(source='step_number')
    targetPage = serializers.CharField(source='target_page')
    targetElement = serializers.CharField(source='target_element')
    estimatedTime = serializers.IntegerField(source='estimated_time')
    isRequired = serializers.BooleanField(source='is_required')
    isActive = serializers.BooleanField(source='is_active')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = OnboardingStep
        fields = ['id', 'stepNumber', 'title', 'description', 'targetPage',
                 'targetElement', 'instructions', 'points', 'category',
                 'estimatedTime', 'isRequired', 'isActive', 'createdAt']


class OnboardingProgressSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source='user_id', read_only=True)
    currentStep = serializers.IntegerField(source='current_step')
    completedSteps = serializers.JSONField(source='completed_steps')
    totalPoints = serializers.IntegerField(source='total_points')
    achievements = serializers.JSONField()
    tutorialCompleted = serializers.BooleanField(source='tutorial_completed')
    lastActiveStep = serializers.CharField(source='last_active_step')
    onboardingStarted = serializers.DateTimeField(source='onboarding_started', read_only=True)
    onboardingCompleted = serializers.DateTimeField(source='onboarding_completed')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = OnboardingProgress
        fields = ['id', 'userId', 'currentStep', 'completedSteps', 'totalPoints',
                 'achievements', 'tutorialCompleted', 'lastActiveStep',
                 'onboardingStarted', 'onboardingCompleted', 'createdAt', 'updatedAt']


class AchievementSerializer(serializers.ModelSerializer):
    isActive = serializers.BooleanField(source='is_active')
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = UserAchievement
        fields = ['id', 'name', 'description', 'icon', 'points', 'category',
                 'condition', 'isActive', 'createdAt']


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'
    # id = serializers.IntegerField()
    # name = serializers.CharField()
    # price = serializers.DecimalField(max_digits=10, decimal_places=2)
    # cameras = serializers.IntegerField()
    # features = serializers.ListField(child=serializers.CharField())


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


class OnboardingCompletionSerializer(serializers.Serializer):
    stepId = serializers.CharField()

    def validate_stepId(self, value):
        valid_steps = ['welcome', 'dashboard', 'cameras', 'alerts', 'ai-chat', 'employees', 'settings']
        if value not in valid_steps:
            raise serializers.ValidationError(f"Invalid stepId. Must be one of: {valid_steps}")
        return value


class RefundRequestSerializer(serializers.Serializer):
    message = serializers.CharField()
    refundId = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    status = serializers.CharField()


class PermissionUpdateSerializer(serializers.ModelSerializer):
    # permissions = serializers.DictField(
    #     child=serializers.BooleanField()
    # )
    class Meta:
        model = MenuPermission
        fields = '__all__'

    # def validate_permissions(self, value):
    #     # valid_permissions = [
    #     #     'dashboard', 'aiChat', 'liveFeed', 'recordings', 
    #     #     'alerts', 'employees', 'zones', 'reports', 'subscription'
    #     # ]
    #     # for key in value.keys():
    #     #     if key not in valid_permissions:
    #     #         raise serializers.ValidationError(f"Invalid permission: {key}")
    #     # return value       
    
    
    def update(self, instance, validated_data):
        print("Updating ", instance)        
        return super().update(instance, validated_data) 

class StatusUpdateSerializer(serializers.Serializer):
    isActive = serializers.BooleanField()


class SubscriptionUpdateSerializer(serializers.ModelSerializer):
    # planName = serializers.CharField()

    class Meta:
        model = Client
        fields = '__all__'
       

class ClientSerializer(serializers.ModelSerializer):   

    subscription_plan = serializers.PrimaryKeyRelatedField(queryset=SubscriptionPlan.objects.all())
    domain = serializers.PrimaryKeyRelatedField(queryset=Domain.objects.all()) 
    class Meta:
        model = Client
        fields  = '__all__'


class ClientNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'name']
        

class ClientUseCaseTypeSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='usecase.type', read_only=True)
    name = serializers.CharField(source='usecase.name', read_only=True)

    class Meta:
        model = ClientUseCase
        fields = ['id', 'severity', 'type', 'name']


class ClientUsecaseSerializer(serializers.ModelSerializer):
    
    usecases = serializers.SerializerMethodField()
    domain = serializers.CharField(source='domain.name', read_only=True)
    class Meta:
        model = Client
        fields  = '__all__'   

    def get_usecases(self, client):       
        usecases = getattr(client, 'filtered_usecases', [])        
        return ClientUseCaseTypeSerializer(usecases, many=True).data