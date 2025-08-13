# ------------------------------------------------------------------------
# Copyright (c) 2025 Piloo.ai
#
# Piloo.ai - AI-Powered CCTV Monitoring Platform
# Copyright © 2025 Pyrack Solutions Pvt. Ltd.
# Website: https://pyrack.com/
# All rights reserved. Proprietary software.
# ------------------------------------------------------------------------
from rest_framework import generics, status, permissions
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from datetime import datetime, timedelta
# from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404


from core.models import (
    UserProfile, Camera, Zone, Alert, Domain
    , Employee, 
    SystemSettings, DemoRequest, SearchQuery, OnboardingProgress,
    OnboardingStep, UserAchievement, SubscriptionPlan
)
from .serializers import *
# import razorpay
from django.conf import settings


class DomainListCreateView(generics.ListCreateAPIView):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    permission_classes = [IsAdminUser]
    
    

class DomainRetrieveUdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    permission_classes = [IsAdminUser]
    
    
class ClientListCreateView(generics.ListCreateAPIView):
    # queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAdminUser]  

    def get_queryset(self):
        return Client.objects.all().order_by('-created_at')    

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except DRFValidationError  as e:            
            error_messages = list(e.detail.values())[0]
            return Response({"detail": error_messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        
        except DjangoValidationError as e:            
            return Response({"detail": e.message_dict.get("name", ["Invalid data"])[0]}, status=status.HTTP_400_BAD_REQUEST)
    
    
"""
@author: Mandar More
@date: 2025-07-25
@description: This view is used to retrieve, update, and delete a client by its primary key (pk).
Changes:
- Replaced ClientSerializer with ClientUsecaseSerializer to include use case data.
- Filters and returns only those client use cases that match the domain of the client.
"""
class ClientRetrieveUdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    # queryset = Client.objects.all()
    serializer_class = ClientUsecaseSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        client_id = self.kwargs.get("pk") 
        client = get_object_or_404(Client, pk=client_id)
        client_domain_id = client.domain_id
        
        return Client.objects.filter(pk=client_id).prefetch_related(
            Prefetch(
                'usecases',
                queryset=ClientUseCase.objects.select_related('usecase').filter(
                    usecase__domain_id=client_domain_id
                ),
                to_attr='filtered_usecases'
            )
        )

"""
@author: Mandar More
@data: 2025-07-17
@description: This view is used to list all clients by name.
"""
class ClientNameListView(generics.ListAPIView):
    serializer_class = ClientNameSerializer
    permission_classes = [IsAuthenticated]    
    pagination_class = None
    
    def get_queryset(self):
        return Client.objects.all().order_by('name')  

  
class AlertTypeMasterListCreateView(generics.ListCreateAPIView):
    serializer_class = AlertTypeMasterSerializer
    permission_classes = [IsAdminUser]
    pagination_class = None
    
    def get_queryset(self):
        client_id = self.request.query_params.get('client')
        if client_id:
            try:
                client = Client.objects.get(id=client_id)
                domain = client.domain
                queryset = AlertTypeMaster.objects.filter(domain=domain)
            except Client.DoesNotExist:
                queryset = AlertTypeMaster.objects.none()
        else:
            queryset = AlertTypeMaster.objects.all()
        return queryset
    
    
class AlertTypeMasterRUDView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AlertTypeMaster.objects.all()
    serializer_class = AlertTypeMasterSerializer
    permission_classes = [IsAdminUser]
    
    
  
class ClientUseCaseListCreateView(generics.ListCreateAPIView):
    queryset = ClientUseCase.objects.all()
    serializer_class = ClientUseCaseSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def create(self, request, *args, **kwargs):
        client = request.data.get('client')
        usecase = request.data.get('usecase')

        if ClientUseCase.objects.filter(client=client, usecase=usecase).exists():
            raise ValidationError({"detail": "This client-usecase combination already exists."})

        return super().create(request, *args, **kwargs)

    
    
class ClientUseCaseRUDView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ClientUseCase.objects.all()
    serializer_class = ClientUseCaseSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
"""
@author: Mandar More
@data: 2025-07-18
@description: This view is used to list all use cases for a specific client.
"""    
class ClientWiseUseCaseListView(generics.ListAPIView):
    serializer_class = ClientUseCaseSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        client_id = self.kwargs.get('client_id')
        return ClientUseCase.objects.filter(client_id=client_id)

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# User Management Views
class UserListCreateView(generics.ListCreateAPIView):
    queryset = UserProfile.objects.all()
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]



# Employee Monitoring Views
class EmployeeListCreateView(generics.ListCreateAPIView):
    serializer_class = EmployeeSerializer
    # permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Employee.objects.filter(company=self.request.user)
        
        # Filter by date if provided
        date_filter = self.request.query_params.get('date')
        if date_filter:
            queryset = queryset.filter(date=date_filter)
        else:
            # Default to today
            queryset = queryset.filter(date=timezone.now().date())
            
        return queryset.order_by('name')
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user)


class EmployeeDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = EmployeeSerializer
    # permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Employee.objects.filter(company=self.request.user)


# System Settings Views
class SystemSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = SystemSettingsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        settings, created = SystemSettings.objects.get_or_create(
            user=self.request.user
        )
        return settings


class SubscriptionPlanListCreateView(generics.ListCreateAPIView):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    
    
    
# Subscription Management Views
class SubscriptionPlansView(APIView):
    def get(self, request):
        # Mock subscription plans
        # plans = [
            # {
            #     'id': 1,
            #     'name': 'Basic',
            #     'price': 29.99,
            #     'cameras': 5,
            #     'features': ['Live Monitoring', 'Basic Alerts', 'Cloud Storage (7 days)']
            # },
        #     {
        #         'id': 2,
        #         'name': 'Professional',
        #         'price': 59.99,
        #         'cameras': 15,
        #         'features': ['Live Monitoring', 'Advanced Alerts', 'Cloud Storage (30 days)', 'AI Analytics']
        #     },
        #     {
        #         'id': 3,
        #         'name': 'Enterprise',
        #         'price': 99.99,
        #         'cameras': -1,  # Unlimited
        #         'features': ['Live Monitoring', 'Advanced Alerts', 'Cloud Storage (90 days)', 'AI Analytics', 'Custom Integration']
        #     }
        # ]
        plans = SubscriptionPlan.objects.all()
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)


class DemoRequestListCreateView(generics.ListCreateAPIView):
    queryset = DemoRequest.objects.all()
    serializer_class = DemoRequestSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated(), IsAdminUser()]
        return []  # Allow anonymous POST for demo requests


# Search Queries Views
class SearchQueryListCreateView(generics.ListCreateAPIView):
    serializer_class = SearchQuerySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = SearchQuery.objects.filter(user=self.request.user)
        user_id = self.request.query_params.get('userId')
        if user_id and str(self.request.user.id) == user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Onboarding Views
class OnboardingProgressView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        progress, created = OnboardingProgress.objects.get_or_create(
            user=request.user,
            defaults={
                'current_step': 1,
                'completed_steps': [],
                'total_points': 0,
                'achievements': [],
                'tutorial_completed': False
            }
        )
        
        serializer = OnboardingProgressSerializer(progress)
        return Response(serializer.data)


class OnboardingStepsView(generics.ListAPIView):
    queryset = OnboardingStep.objects.filter(is_active=True).order_by('step_number')
    serializer_class = OnboardingStepSerializer
    permission_classes = [IsAuthenticated]


class CompleteOnboardingStepView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, step_id):
        # Define step points
        step_points = {
            'welcome': 10,
            'dashboard': 20,
            'cameras': 30,
            'alerts': 25,
            'ai-chat': 35,
            'employees': 20,
            'settings': 15
        }
        
        if step_id not in step_points:
            return Response(
                {'error': 'Invalid step ID'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        progress, created = OnboardingProgress.objects.get_or_create(
            user=request.user,
            defaults={
                'current_step': 1,
                'completed_steps': [],
                'total_points': 0,
                'achievements': [],
                'tutorial_completed': False
            }
        )
        
        # Add step to completed steps if not already completed
        if step_id not in progress.completed_steps:
            progress.completed_steps.append(step_id)
            progress.total_points += step_points[step_id]
            progress.last_active_step = step_id
            progress.save()
        
        response_data = {
            'message': f'Step {step_id} completed successfully',
            'stepId': step_id,
            'pointsEarned': step_points[step_id]
        }
        
        return Response(response_data)


# Achievement Views
class AchievementListView(generics.ListAPIView):
    queryset = UserAchievement.objects.filter(is_active=True)
    serializer_class = AchievementSerializer
    permission_classes = [IsAuthenticated]


class AwardAchievementView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, achievement_id):
        try:
            achievement = UserAchievement.objects.get(id=achievement_id, is_active=True)
        except UserAchievement.DoesNotExist:
            return Response(
                {'error': 'Achievement not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user already has this achievement
        user_achievement, created = UserAchievement.objects.get_or_create(
            user=request.user,
            achievement=achievement
        )
        
        if created:
            # Update user's onboarding progress
            progress, _ = OnboardingProgress.objects.get_or_create(
                user=request.user,
                defaults={
                    'current_step': 1,
                    'completed_steps': [],
                    'total_points': 0,
                    'achievements': [],
                    'tutorial_completed': False
                }
            )
            
            if achievement.id not in progress.achievements:
                progress.achievements.append(achievement.id)
                progress.total_points += achievement.points
                progress.save()
        
        response_data = {
            'id': user_achievement.id,
            'userId': request.user.id,
            'totalPoints': OnboardingProgress.objects.get(user=request.user).total_points,
            'achievements': OnboardingProgress.objects.get(user=request.user).achievements
        }
        
        return Response(response_data)


# Admin Management Panel Views
class AdminClientListView(generics.ListAPIView):
    queryset = UserProfile.objects.all()
    # serializer_class = AdminUserSerializer
    # Mandar - Create a new serializer for admin client list
    serializer_class = AdminClientSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        return UserProfile.objects.filter(is_superuser=False).order_by('-date_joined')


class AdminClientDetailView(generics.RetrieveUpdateAPIView):
    queryset = UserProfile.objects.all()
    # serializer_class = AdminUserSerializer
    serializer_class = AdminClientSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

class AdminClientStatusView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def put(self, request, pk):
        try:
            user = UserProfile.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = StatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            user.is_active = serializer.validated_data['isActive']
            user.save()
            
            status_text = 'activated' if user.is_active else 'deactivated'
            return Response({
                'message': f'User account has been {status_text} successfully'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminClientPermissionsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def put(self, request, pk):
        try:
            user = UserProfile.objects.get(pk=pk)
            # profile = user.userprofile
            profile = user.menu_permissions
        except (UserProfile.DoesNotExist, UserProfile.DoesNotExist):
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # serializer = PermissionUpdateSerializer(data=request.data)
        serializer = PermissionUpdateSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            # profile.menu_permissions = serializer.validated_data['permissions']
            # for key, value in serializer.validated_data['permissions'].items():
            #     setattr(profile, key, value)

            serializer.save()
            
            return Response({
                'message': 'User permissions updated successfully',
                'permissions': serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminClientRefundView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def post(self, request, pk):
        try:
            user = UserProfile.objects.get(pk=pk)
            profile = user.userprofile
        except (UserProfile.DoesNotExist, UserProfile.DoesNotExist):
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # This would integrate with Stripe for actual refund processing
        # For now, returning mock response
        refund_data = {
            'message': 'Refund processed successfully',
            'refundId': f'rf_{user.id}_{timezone.now().timestamp()}',
            'amount': 59.99,  # This would come from actual subscription
            'status': 'succeeded'
        }
        
        # Update user subscription status
        profile.subscription_plan = None
        profile.subscription_status = 'cancelled'
        profile.subscription_ends_at = timezone.now()
        profile.save()
        
        serializer = RefundRequestSerializer(refund_data)
        return Response(serializer.data)


class AdminCreateClientView(generics.CreateAPIView):
    # queryset = UserProfile.objects.all()
    # serializer_class = UserCreateSerializer
    # permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = UserProfile.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Client user created successfully',
                'user': UserCreateSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminDeleteClientView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def delete(self, request, pk):
        try:
            user = UserProfile.objects.get(pk=pk)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )        
        
        user.delete()
        
        return Response(
            {'message': 'User deleted successfully'}, 
            status=status.HTTP_204_NO_CONTENT
        )
            
class AdminClientSubscriptionView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    # def put(self, request, pk):
    #     try:
    #         user = UserProfile.objects.get(pk=pk)
    #         profile = user.userprofile
    #     except (UserProfile.DoesNotExist, UserProfile.DoesNotExist):
    #         return Response(
    #             {'error': 'User not found'}, 
    #             status=status.HTTP_404_NOT_FOUND
    #         )
        
    #     serializer = SubscriptionUpdateSerializer(data=request.data)
    #     if serializer.is_valid():
    #         plan_name = serializer.validated_data['planName']
            
    #         # Update subscription plan
    #         profile.subscription_plan = plan_name
    #         profile.subscription_status = 'active'
            
    #         # Set camera limits based on plan
    #         plan_limits = {
    #             'Basic': 5,
    #             'Professional': 15,
    #             'Enterprise': 999  # Representing unlimited
    #         }
    #         profile.max_cameras = plan_limits.get(plan_name, 1)
    #         profile.save()
            
    #         response_serializer = UserSerializer(user)
    #         return Response(response_serializer.data)
        
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        try:
            user = UserProfile.objects.get(pk=pk)
            client = user.company
            if not client:
                return Response({'error': 'User is not linked to any client'}, status=400)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        serializer = SubscriptionUpdateSerializer(client, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Subscription updated successfully',
                'client': serializer.data
            })
        
        return Response(serializer.errors, status=400)

# Additional Analytics Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def occupancy_analytics(request):
    user = request.user
    zones = Zone.objects.filter(owner=user)
    
    occupancy_data = []
    for zone in zones:
        # This would typically involve people counting from camera feeds
        # For now, using mock data
        occupancy_data.append({
            'zone': zone.name,
            'occupancy': 8,  # Mock current occupancy
            'capacity': 20,  # Mock zone capacity
            'percentage': 40.0  # Mock percentage
        })
    
    serializer = OccupancySerializer(occupancy_data, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def camera_performance(request):
    user = request.user
    cameras = Camera.objects.filter(owner=user)
    
    performance_data = []
    for camera in cameras:
        # Calculate performance metrics
        total_alerts = Alert.objects.filter(camera=camera).count()
        
        performance_data.append({
            'id': camera.id,
            'name': camera.name,
            'uptime': 99.5,  # Mock uptime percentage
            'alerts': total_alerts,
            'lastMaintenance': timezone.now() - timedelta(days=30),  # Mock
            'status': camera.status
        })
    
    serializer = CameraPerformanceSerializer(performance_data, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def activity_heatmap(request):
    user = request.user
    
    # This would typically analyze activity patterns from alerts/recordings
    # For now, returning mock heatmap data
    heatmap_data = []
    
    for hour in range(24):
        hour_str = f"{hour:02d}:00"
        heatmap_data.append({
            'hour': hour_str,
            'monday': hour * 2,
            'tuesday': hour * 1.5,
            'wednesday': hour * 2.2,
            'thursday': hour * 1.8,
            'friday': hour * 2.5,
            'saturday': hour * 1.2,
            'sunday': hour * 0.8
        })
    
    serializer = ActivityHeatmapSerializer(heatmap_data, many=True)
    return Response(serializer.data)

