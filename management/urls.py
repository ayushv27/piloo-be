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
#manage/

urlpatterns = [
    #ml model/ domain
    path('v1/domains/', views.DomainListCreateView.as_view(), name='admin-client-list'),
    path('v1/domain/<int:pk>/', views. DomainRetrieveUdateDeleteView.as_view(), name='admin-client-update-retrieve-delete'),
    
    #client managment
    path('v1/clients/', views.ClientListCreateView.as_view(), name='admin-client-list'),
    path('v1/client/<str:pk>/', views.ClientRetrieveUdateDeleteView.as_view(), name='admin-client-update-retrieve-delete'),
    path('v1/clientsname/', views.ClientNameListView.as_view(), name='admin-client-list'),
    
    #use cases management
    path('v1/alertmaster/', views.AlertTypeMasterListCreateView.as_view(), name='admin-client-list'),
    path('v1/alertmaster/<int:pk>/', views. AlertTypeMasterRUDView.as_view(), name='admin-client-update-retrieve-delete'),
    path('v1/clientusecases/', views.ClientUseCaseListCreateView.as_view(), name='admin-client-list'),
    path('v1/clientusecase/<int:pk>/', views.ClientUseCaseRUDView.as_view(), name='admin-client-update-retrieve-delete'),
    path('v1/client-usecases/<uuid:client_id>/',views.ClientWiseUseCaseListView.as_view(),name='client-usecase-list'),
    
    # Employee monitoring
    path('api/employees/', views.EmployeeListCreateView.as_view(), name='employee-list-create'),
    path('api/employees/<int:pk>/', views.EmployeeDetailView.as_view(), name='employee-detail'),
    
    # System settings
    path('api/settings/', views.SystemSettingsView.as_view(), name='system-settings'),
    
    # Subscription management
    path('api/subscription-plans/', views.SubscriptionPlansView.as_view(), name='subscription-plans'),
    path('v1/subscriptionplans/', views.SubscriptionPlanListCreateView.as_view(), name='list or POSt plans'),
    path('api/demo-requests/', views.DemoRequestListCreateView.as_view(), name='demo-requests'),
 
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
    # path('api/admin/clients/', views.AdminCreateClientView.as_view(), name='admin-create-client'),
    path('api/admin/clients/creat/', views.AdminCreateClientView.as_view(), name='admin-create-client'),
    path('api/admin/clients/<int:pk>/subscription/', views.AdminClientSubscriptionView.as_view(), name='admin-client-subscription'),
    #  mandar - Delete client
    path('api/admin/clients/<int:pk>/delete/', views.AdminDeleteClientView.as_view(), name='admin-delete-client'),
    
]
