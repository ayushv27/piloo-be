from django.contrib import admin
from .models import *


models = [
    Client,
    UserProfile,
    ClientUseCase,
    Zone,
    Camera,
    Alert,
    Recording,
    SubscriptionPlan,
    MenuPermission,
    OnboardingProgress,
    SystemSettings,
    Domain,
    
    AlertTypeMaster,
    TempNotification
]

for model in models:
    admin.site.register(model)  
