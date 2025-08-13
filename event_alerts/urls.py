from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QdrantTodayDataView, FetchAlertsAPIView, GroupedAlertsView, ClientAlertTypesAPIView

urlpatterns = [

   
    path('api/fetch-events/', GroupedAlertsView.as_view(), name='grouped-alerts'),#FE done
    path('test-fetch-alerts/', FetchAlertsAPIView.as_view(), name='test-fetch-alerts'),
    path('api/today-data/', QdrantTodayDataView.as_view(), name='today-data'),
    path("api/client-alert-types/", ClientAlertTypesAPIView.as_view(), name="client-alert-types"),#FE done
    
]