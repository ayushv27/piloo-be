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

#auth
# API URL patterns
urlpatterns = [
    # path('csrf/', views.csrf_token_view, name='GET CSRF token'),
    # path('getcookie/', views.set_cookie_view, name='get session cookie'),
    # Authentication endpoints
    path('v1/login/', views.LoginView.as_view(), name='login'),
    path('v1/otpverify/', views.OtpVerify.as_view(), name='login'),
    # path("v2/login/", views.CustomTokenObtainPairView.as_view(), name="login"),
    # path('sendemailverification/', views.SendEmailVerificationsView, name='get email verification mail'),
    # path('verifyemail', views.VerifyEmailView, name='verify email'),
    path('v1/logout/', views.LogoutView.as_view(), name='logout'),
    path('v1/user/', views.CurrentUserView.as_view(), name='current-user'),
    
    # User management
    path('v1/users/', views.UserListCreateView.as_view(), name='user-list-create'),
    path('v1/users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    
    # email verification
    path('v1/email/send-verification/', views.SendEmailVerificationView.as_view(), name='send-email-verification'),
    path('v1/email/verify/', views.EmailVerificationView.as_view(), name='email-verification'),
    
    #reset password
    path('v1/password-reset/', views.PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('login/<str:token>', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),



    # Employee monitoring
    path('api/employees/', views.EmployeeListCreateView.as_view(), name='employee-list-create'),
    path('api/employees/<int:pk>/', views.EmployeeDetailView.as_view(), name='employee-detail'),
    
    # System settings
    path('api/settings/', views.SystemSettingsView.as_view(), name='system-settings'),
    
    # Dashboard statistics
    path('api/stats/', views.dashboard_stats, name='dashboard-stats'),
    
    # Analytics endpoints
    path('api/analytics/', views.analytics_overview, name='analytics-overview'),
    path('api/analytics/incident-trends/', views.incident_trends, name='incident-trends'),
    path('api/analytics/alert-distribution/', views.alert_distribution, name='alert-distribution'),
    path('api/analytics/occupancy/', views.occupancy_analytics, name='occupancy-analytics'),
    path('api/analytics/camera-performance/', views.camera_performance, name='camera-performance'),
    path('api/analytics/activity-heatmap/', views.activity_heatmap, name='activity-heatmap'),
    
    # AI search integration
    path('api/cctv/ask/', views.CCTVSearchView.as_view(), name='cctv-search'),
    
    # Subscription management
    path('api/subscription-plans/', views.SubscriptionPlansView.as_view(), name='subscription-plans'),
    path('api/demo-requests/', views.DemoRequestListCreateView.as_view(), name='demo-requests'),
    path("api/subscription_plans/", views.ClientSubscriptionPlanView.as_view(), name="user-subscription-plans"),
    
    # Search queries
    path('api/search-queries/', views.SearchQueryListCreateView.as_view(), name='search-queries'),
    
    # User onboarding
    path('api/user/onboarding/', views.OnboardingProgressView.as_view(), name='onboarding-progress'),
    path('api/user/onboarding/complete/', views.CompleteOnboardingStepView.as_view(), name='complete-onboarding-step'),
    path('api/onboarding/steps/', views.OnboardingStepsView.as_view(), name='onboarding-steps'),
    path('api/onboarding/complete-step/<str:step_id>/', views.CompleteOnboardingStepView.as_view(), name='complete-step'),
    
    # Achievement system
    path('api/achievements/', views.AchievementListView.as_view(), name='achievements'),
    path('api/achievements/award/<int:achievement_id>/', views.AwardAchievementView.as_view(), name='award-achievement'),
    
    # Management panel (Admin)
    path('api/admin/clients/', views.AdminClientListView.as_view(), name='admin-client-list'),
    path('api/admin/clients/<int:pk>/', views.AdminClientDetailView.as_view(), name='admin-client-detail'),
    path('api/admin/clients/<int:pk>/status/', views.AdminClientStatusView.as_view(), name='admin-client-status'),
    path('api/admin/clients/<int:pk>/permissions/', views.AdminClientPermissionsView.as_view(), name='admin-client-permissions'),
    path('api/admin/clients/<int:pk>/refund/', views.AdminClientRefundView.as_view(), name='admin-client-refund'),
    path('api/admin/clients/', views.AdminCreateClientView.as_view(), name='admin-create-client'),
    path('api/admin/clients/<int:pk>/subscription/', views.AdminClientSubscriptionView.as_view(), name='admin-client-subscription'),
    
    
    # razorpay payment integration
    path('api/payment/razorpay/create-order/', views.CreateRazorpayOrderView.as_view(), name='razorpay-create-order'),
    path('api/payment/razorpay/verify-payment/', views.VerifyRazorpayPaymentView.as_view(), name='razorpay-verify-payment'),


    
]

# WebSocket URL patterns (if using Django Channels)
# websocket_urlpatterns = [
#     path('ws/', views.WebSocketConsumer.as_asgi()),  # This would be defined in consumers.py
# ]