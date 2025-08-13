# ------------------------------------------------------------------------
# Copyright (c) 2025 Piloo.ai
#
# Piloo.ai - AI-Powered CCTV Monitoring Platform
# Copyright © 2025 Pyrack Solutions Pvt. Ltd.
# Website: https://pyrack.com/
# All rights reserved. Proprietary software.
# ------------------------------------------------------------------------

import random
from rest_framework import generics, status, permissions
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    UserProfile, Camera, Zone, Alert, Recording, Employee, 
    SystemSettings, DemoRequest, SearchQuery, OnboardingProgress,
    OnboardingStep, UserAchievement, PasswordResetToken, ClientPayment, SubscriptionPlan
)
from .serializers import *
from rest_framework.response import Response
from django.core.cache import cache
from rest_framework.generics import GenericAPIView
from . utils import send_reset_email
from django.utils.timezone import now 
from  .tasks import send_email_otp
import razorpay

# Authentication Views
class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        print(request.data)
        response = Response()
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, _ = Token.objects.get_or_create(user=user)
            print('token', token.key)
            otp = random.randint(100000, 999999)
            cache.set(user.email, otp, timeout=600)  # 10 minutes
            print('otp::', otp)
            #celery task to send email
            send_email_otp.delay(user.email, otp)
            print('otp sent')
            user = UserProfile.objects.get(email=user.email)
            user.otp = otp
            user.save()
            print(user.otp)
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'otp': otp,
                'client_name': getattr(user.company, 'name', None) if getattr(user, 'company', 'user') is not None else 'Demo Client',
                'role': getattr(user, 'role', 'user'),
                'domain': getattr(user.company.domain, 'name', None) if getattr(user, 'company', 'user') is not None else 'admin',
                'subscriptionPlan': getattr(user.company.subscription_plan_id, 'name', None) if getattr(user, 'role', 'user')!='admin' else 'admin',
                'token': token.key
            }
            return Response({'user': user_data}, status=status.HTTP_200_OK)
        else:
            errors = serializer.errors           
            if isinstance(errors, dict) and "non_field_errors" in errors:
                error_message = errors["non_field_errors"][0]
                return Response({"detail": str(error_message)}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"detail": str(errors)}, status=status.HTTP_400_BAD_REQUEST)
            # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OtpVerify(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        print(request.data)
        response = Response()
        print(request.data)
        serializer = VerifyOPTSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, _ = Token.objects.get_or_create(user=user)
            print('token', token.key)
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'client_name': getattr(user.company, 'name', None) if getattr(user, 'company', 'user') is not None else 'Demo Client',
                'role': getattr(user, 'role', 'user'),
                'domain': getattr(user.company.domain, 'name', None) if getattr(user, 'company', 'user') is not None else 'admin',
                'subscriptionPlan': getattr(user.company.subscription_plan_id, 'name', None) if getattr(user, 'role', 'user')!='admin' else 'admin',
                'token': token.key
            }
            return Response({'user': user_data}, status=status.HTTP_200_OK)
        else:
            errors = serializer.errors           
            if isinstance(errors, dict) and "non_field_errors" in errors:
                error_message = errors["non_field_errors"][0]
                return Response({"detail": str(error_message)}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": str(errors)}, status=status.HTTP_400_BAD_REQUEST)
        

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        pass
        # logout(request)
        try:
            token = Token.objects.get(user=request.user)
            token.delete()
        except Token.DoesNotExist:
            pass  # Token may already be deleted
        return Response({'detail': 'User logged out successfully.'}, status=status.HTTP_200_OK)


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
    
    

# class SendEmailVerificationsView(APIView):
#     def post(self, request):
#         serializer = EmailVerifySerializer(data=request.data, context={'request': request})
#         serializer.is_valid(raise_exception=True)
#         return Response({'message': 'Registration successful. Check email to verify.'}, status=status.HTTP_201_CREATED)


# class VerifyEmailView(APIView):
#     def get(self, request):
#         token = request.GET.get('token')
#         try:
#             user_id = AccessToken(token)['user_id']
#             user = User.objects.get(id=user_id)
#             if user.is_verified:
#                 return Response({'message': 'Account already verified.'})
#             user.is_verified = True
#             user.save()
#             return Response({'message': 'Email verified successfully.'})
#         except Exception:
#             raise AuthenticationFailed('Invalid or expired token')
        
        
class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]



# Employee Monitoring Views
class EmployeeListCreateView(generics.ListCreateAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]
    
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
    permission_classes = [IsAuthenticated]
    
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


# Dashboard Statistics View
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    user = request.user
    today = timezone.now().date()
    
    # Calculate statistics
    active_cameras = Camera.objects.filter(owner=user, status='active').count()
    today_incidents = Alert.objects.filter(
        camera__owner=user, 
        timestamp__date=today
    ).count()
    current_alerts = Alert.objects.filter(
        camera__owner=user, 
        status='active'
    ).count()
    
    # Employee stats
    employees_today = Employee.objects.filter(company=user, date=today)
    employee_stats = {
        'present': employees_today.filter(status='present').count(),
        'absent': employees_today.filter(status='absent').count(),
        'late': employees_today.filter(status='late').count(),
        'avgDuration': '8h 30m'  # This would be calculated based on check-in/out times
    }
    
    # Zone coverage calculation
    total_zones = Zone.objects.filter(owner=user).count()
    covered_zones = Camera.objects.filter(
        owner=user, 
        status='active'
    ).values('assigned_zone').distinct().count()
    
    zone_coverage = f"{covered_zones}/{total_zones} zones"
    
    stats = {
        'activeCameras': active_cameras,
        'todayIncidents': today_incidents,
        'currentAlerts': current_alerts,
        'zoneCoverage': zone_coverage,
        'employeeStats': employee_stats
    }
    
    serializer = StatsSerializer(stats)
    return Response(serializer.data)


# Analytics Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_overview(request):
    user = request.user
    today = timezone.now().date()
    
    alerts = Alert.objects.filter(camera__owner=user)
    
    analytics = {
        'totalIncidents': alerts.count(),
        'todayIncidents': alerts.filter(timestamp__date=today).count(),
        'activeCameras': Camera.objects.filter(owner=user, status='active').count(),
        'criticalAlerts': alerts.filter(usecase__severity='critical', status='active').count(),
        'resolvedIncidents': alerts.filter(status='resolved').count(),
        'avgResponseTime': 15  # This would be calculated from alert resolution times
    }
    
    serializer = AnalyticsSerializer(analytics)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def incident_trends(request):
    user = request.user
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # This would typically involve complex aggregation queries
    # For now, returning sample data structure
    trends = []
    current_date = start_date
    
    while current_date <= end_date:
        daily_alerts = Alert.objects.filter(
            camera__owner=user,
            timestamp__date=current_date
        )
        
        trend_data = {
            'date': current_date.strftime('%Y-%m-%d'),
            'incidents': daily_alerts.count(),
            'resolved': daily_alerts.filter(status='resolved').count(),
            'critical': daily_alerts.filter(usecase__severity='critical').count(),
            'high': daily_alerts.filter(usecase__severity='high').count(),
            'medium': daily_alerts.filter(usecase__severity='medium').count(),
            'low': daily_alerts.filter(usecase__severity='low').count(),
        }
        trends.append(trend_data)
        current_date += timedelta(days=1)
    
    serializer = IncidentTrendSerializer(trends, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def alert_distribution(request):
    user = request.user
    
    alert_counts = Alert.objects.filter(camera__owner=user).values('label').annotate(
        count=Count('label')
    )
    
    total_alerts = sum(item['count'] for item in alert_counts)
    
    distribution = []
    for item in alert_counts:
        distribution.append({
            'name': item['label'],
            'value': item['count'],
            'percentage': round((item['count'] / total_alerts) * 100, 2) if total_alerts > 0 else 0
        })
    
    serializer = AlertDistributionSerializer(distribution, many=True)
    return Response(serializer.data)


# AI Search Integration
class CCTVSearchView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CCTVSearchSerializer(data=request.data)
        if serializer.is_valid():
            query = serializer.validated_data['query']
            camera_ids = serializer.validated_data.get('cameraIds', [])
            time_range = serializer.validated_data.get('timeRange', {})
            
            # Filter user's cameras
            user_cameras = Camera.objects.filter(owner=request.user)
            if camera_ids:
                user_cameras = user_cameras.filter(id__in=camera_ids)
            
            # This would integrate with AI/ML service for video analysis
            # For now, returning mock results based on recordings and alerts
            results = []
            
            # Search in recordings and alerts
            recordings = Recording.objects.filter(camera__in=user_cameras)
            alerts = Alert.objects.filter(camera__in=user_cameras)
            
            if time_range:
                start_time = time_range.get('start')
                end_time = time_range.get('end')
                if start_time:
                    recordings = recordings.filter(start_time__gte=start_time)
                    alerts = alerts.filter(timestamp__gte=start_time)
                if end_time:
                    recordings = recordings.filter(end_time__lte=end_time)
                    alerts = alerts.filter(timestamp__lte=end_time)
            
            # Mock AI search results
            for alert in alerts[:5]:  # Limit results
                results.append({
                    'timestamp': alert.timestamp,
                    'cameraId': alert.camera.id,
                    'cameraName': alert.camera.name,
                    'description': alert.description,
                    'confidence': 0.85,  # Mock confidence score
                    'videoUrl': alert.chunk_url or '',
                    'thumbnailUrl': f'/api/thumbnails/alert_{alert.id}.jpg'
                })
            
            response_data = {
                'results': results,
                'summary': f'Found {len(results)} matches for "{query}"',
                'totalResults': len(results)
            }
            
            # Save search query
            SearchQuery.objects.create(
                user=request.user,
                query=query,
                filters=serializer.validated_data,
                results=len(results)
            )
            
            response_serializer = CCTVSearchResponseSerializer(response_data)
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Subscription Management Views
class SubscriptionPlansView(APIView):
    def get(self, request):
        # Mock subscription plans
        plans = [
            {
                'id': 1,
                'name': 'Basic',
                'price': 29.99,
                'cameras': 5,
                'features': ['Live Monitoring', 'Basic Alerts', 'Cloud Storage (7 days)']
            },
            {
                'id': 2,
                'name': 'Professional',
                'price': 59.99,
                'cameras': 15,
                'features': ['Live Monitoring', 'Advanced Alerts', 'Cloud Storage (30 days)', 'AI Analytics']
            },
            {
                'id': 3,
                'name': 'Enterprise',
                'price': 99.99,
                'cameras': -1,  # Unlimited
                'features': ['Live Monitoring', 'Advanced Alerts', 'Cloud Storage (90 days)', 'AI Analytics', 'Custom Integration']
            }
        ]
        
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)


class DemoRequestListCreateView(generics.ListCreateAPIView):
    queryset = DemoRequest.objects.all()
    serializer_class = DemoRequestSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated(), IsAdminUser()]
        return []  # Allow anonymous POST for demo requests

"""
@author: Mandar More
@date: 07-07-2025
@description: View to get the subscription plan of the user.
"""
class ClientSubscriptionPlanView(generics.RetrieveAPIView):
    serializer_class = ClientSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]   

    def get_object(self):
        return self.request.user.company

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
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        return UserProfile.objects.filter(is_superuser=False).order_by('-date_joined')


class AdminClientDetailView(generics.RetrieveUpdateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = AdminUserSerializer
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
            profile = user.userprofile
        except (UserProfile.DoesNotExist, UserProfile.DoesNotExist):
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = PermissionUpdateSerializer(data=request.data)
        if serializer.is_valid():
            profile.menu_permissions = serializer.validated_data['permissions']
            profile.save()
            
            return Response({
                'message': 'User permissions updated successfully'
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
    queryset = UserProfile.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class AdminClientSubscriptionView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def put(self, request, pk):
        try:
            user = UserProfile.objects.get(pk=pk)
            profile = user.userprofile
        except (UserProfile.DoesNotExist, UserProfile.DoesNotExist):
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SubscriptionUpdateSerializer(data=request.data)
        if serializer.is_valid():
            plan_name = serializer.validated_data['planName']
            
            # Update subscription plan
            profile.subscription_plan = plan_name
            profile.subscription_status = 'active'
            
            # Set camera limits based on plan
            plan_limits = {
                'Basic': 5,
                'Professional': 15,
                'Enterprise': 999  # Representing unlimited
            }
            profile.max_cameras = plan_limits.get(plan_name, 1)
            profile.save()
            
            response_serializer = UserSerializer(user)
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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



"""
@author: Neha Pawar
@date: 23-06-2025
@description: View to send email verification OTP to the user.
"""  
class SendEmailVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        otp = random.randint(100000, 999999)
        cache.set(email, otp, timeout=600)  # 10 minutes
        print('otp::', otp)
        #celery task to send email
        send_email_otp.delay(email, otp)

        return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)
    
"""
@author: Neha Pawar
@date: 23-06-2025
@description: View to verify the email using the OTP sent to the user.
""" 
class EmailVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email or not otp:
            return Response({'detail': 'Email and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)

        cached_otp = cache.get(email)
        if cached_otp is None:
            return Response({'detail': 'OTP expired or not found'}, status=status.HTTP_400_BAD_REQUEST)

        if str(cached_otp) != str(otp):
            return Response({'detail': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = UserProfile.objects.get(email=email)
        except UserProfile.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        user.is_verified = True
        user.save()

        cache.delete(email)

        return Response({'message': 'Email verified successfully'}, status=status.HTTP_200_OK)
    
"""
@author: Neha Pawar
@date: 23-06-2025
@description: View to handle password reset requests.
"""  
class PasswordResetRequestView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = UserProfile.objects.get(email=email)
        except UserProfile.DoesNotExist:
            return Response(
                {"detail": "User with this email does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )
        referer = request.META.get('HTTP_REFERER')
        if referer:
            domain = referer.split('/')[2] 
        else:
            domain = request.get_host()
        # Create reset token and send email
        reset_token = PasswordResetToken.objects.create(user=user)
        print('reset_token--', reset_token.token)
        send_reset_email(user, reset_token, domain)

        return Response(
            {"message": "Password reset email has been sent."},
            status=status.HTTP_200_OK
        )

            
            
"""
@author : Neha Pawar
@date : 23-06-2025
@description: View to handle password reset confirmation.
"""         
class PasswordResetConfirmView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_value = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        confirm_pass = serializer.validated_data['confirm_password']
        if new_password != confirm_pass:
            return Response(
                {"detail": "New password and confirmation do not match."},
                status=status.HTTP_400_BAD_REQUEST
            )
       
        try:
            token = PasswordResetToken.objects.get(token=token_value, is_used=False)
        except PasswordResetToken.DoesNotExist:
            return Response(
                {"detail": "Invalid or used reset token."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check token expiry
        if now() > token.created_at + timedelta(hours=24):
            return Response(
                {"detail": "Reset token has expired."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Reset password
        user = token.user
        user.set_password(new_password)
        user.save()

        token.is_used = True
        token.save()

        return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)
    
    
"""
@author: Neha Pawar
@date: 02-07-2025
@description: View to create Razorpay order for subscription payment.
"""
class CreateRazorpayOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        client = request.user.company
        plan_id = request.data.get("subscription_plan_id")

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response({"error": "Invalid subscription plan."}, status=400)

        amount = int(plan.price * 100) # Convert to paise for Razorpay
        client_obj = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET))
        
        # Step 1: Create order with Razorpay
        razorpay_order = client_obj.order.create({
            "amount": amount,
            "currency": "INR",
            "receipt": f"receipt_{datetime.now().timestamp()}",
            "payment_capture": 1
        })

        # Step 2: Create local payment record
        payment = ClientPayment.objects.create(
            client=client,
            subscription_plan=plan,
            amount=plan.price,
            razorpay_order_id=razorpay_order['id'],
            status='created'
        )

        return Response({
            "order_id": razorpay_order['id'],
            "amount": amount,
            "currency": "INR",
            "razorpay_key": settings.RAZORPAY_KEY_ID
        })
        

"""
@author: Neha Pawar
@date: 02-07-2025
@description: View to verify Razorpay payment and activate subscription.
"""
class VerifyRazorpayPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        client = request.user.company

        try:
            payment = ClientPayment.objects.get(
                razorpay_order_id=data['razorpay_order_id'],
                client=client
            )
        except ClientPayment.DoesNotExist:
            return Response({"error": "Payment record not found."}, status=404)

        client_obj = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET))

        try:
            # Step 1: Verify signature
            client_obj.utility.verify_payment_signature({
                'razorpay_order_id': data['razorpay_order_id'],
                'razorpay_payment_id': data['razorpay_payment_id'],
                'razorpay_signature': data['razorpay_signature']
            })

            # Step 2: Mark as paid
            payment.razorpay_payment_id = data['razorpay_payment_id']
            payment.razorpay_signature = data['razorpay_signature']
            payment.status = 'success'
            payment.paid_at = datetime.now()
            payment.save()

            # Step 3: Activate subscription
            client.subscription_plan = payment.subscription_plan # updating the subscription plan 
            client.subscription_status = 'active'
            client.subscription_ends_at = datetime.now().date() + timedelta(days=payment.subscription_plan.subscription_days)
            client.save()

            return Response({"message": "Payment verified and subscription activated."})

        except razorpay.errors.SignatureVerificationError:
            payment.status = 'failed'
            payment.save()
            return Response({"error": "Payment verification failed."}, status=400)



    