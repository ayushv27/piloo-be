from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import uuid
from django.http import FileResponse, Http404

from core.models import Camera, Zone, Alert, Recording, AlertTypeMaster
from .serializers import *
# from core.managers import AuthCookieMixin
from django.utils.timezone import make_aware
from datetime import datetime, time, timedelta
from django.db.models import Q, TimeField, Min
from django.db.models.functions import Cast
from rest_framework.exceptions import ParseError
from collections import defaultdict
from django.core.exceptions import ObjectDoesNotExist
# from core.pagination import CustomPageNumberPagination
import os
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter, OpenApiTypes
import boto3
from django.conf import settings
# Create your views here.


# Camera Management Views
class CameraListCreateView(generics.ListCreateAPIView):
    serializer_class = CameraSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        zone_id = self.request.query_params.get("zone_id", None)
        camera_id = self.request.query_params.get("camera_id", None)

        if user.role == "admin":
            queryset = Camera.objects.all().order_by('-created_at')
        else:
            queryset = Camera.objects.filter(owner=user.company).order_by('-created_at')

        if zone_id and zone_id.lower() != "all-zones":
            queryset = queryset.filter(assigned_zone__id=zone_id)

        if camera_id and camera_id.lower() != "all-cameras":
            try:
                camera_uuid = uuid.UUID(camera_id)
                queryset = queryset.filter(id=camera_uuid)
            except ValueError:
                queryset = queryset.none()

        return queryset        


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save(owner=request.user.company)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:            
            if hasattr(e, 'detail'):
                errors = e.detail
                if isinstance(errors, dict):
                    non_field_errors = errors.get('non_field_errors')
                    if non_field_errors:
                        return Response({"error": str(non_field_errors[0])}, status=status.HTTP_400_BAD_REQUEST)
                return Response({"error": str(errors)}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        
class CameraNameListView(generics.ListAPIView):
    serializer_class = CameraNameSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    
    def get_queryset(self):
        user = self.request.user
        zone_id = self.request.query_params.get("zone_id", None)        
        queryset = (
            Camera.objects.select_related("assigned_zone").all()
            if user.role == "admin"
            else Camera.objects.select_related("assigned_zone").filter(owner=user.company)
        )

        if zone_id and zone_id.lower() != "all-zones":
            queryset = queryset.filter(assigned_zone__id=zone_id)

        return queryset.order_by("name")
     

class CameraListView(generics.ListAPIView):
    serializer_class = CameraSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Camera.objects.filter(status='active')   


class ChangeCameraStatusView(generics.UpdateAPIView):
    serializer_class = CameraSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        status = request.data.get('status', None)
        if status == 'offline':
            
            
            pass
        pass 


class CameraDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CameraSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        print(user, user.company)
        return Camera.objects.filter(owner=user.company)
    
    
    def perform_update(self, serializer):
        print('data', self.request.data)
        if not serializer.instance.owner:
            serializer.save(owner=self.request.user.company)
        else:
            serializer.save()


# Zone Management Views
class ZoneListCreateView(generics.ListCreateAPIView):
    serializer_class = ZoneSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return Zone.objects.all()
        else:
            return Zone.objects.filter(owner=user.company)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save(owner=request.user.company)  # Direct save here
            return Response(serializer.data, status=status.HTTP_201_CREATED)      
        
        except Exception as e:
            # return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)


     
class ZoneNameListView(generics.ListAPIView):
    serializer_class = ZoneNameSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    
    def get_queryset(self):
        user = self.request.user   
        queryset = Zone.objects.filter(owner=user.company)
            

        return queryset.order_by("name")
    
    
class ZoneDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ZoneSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Zone.objects.filter(owner=user.company)


# Alert Management Views
@extend_schema_view(
    get=extend_schema(
        tags=["Alerts"],
        summary="List Alerts",
        description="Retrieve a filtered list of alerts for the authenticated user.",
        parameters=[
            OpenApiParameter(name="fromDate", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="fromTime", type=OpenApiTypes.TIME, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="toDate", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="toTime", type=OpenApiTypes.TIME, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="eventType", type=str, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="cameraName", type=str, location=OpenApiParameter.QUERY),
        ],
    ),
    post=extend_schema(
        summary="Create Alert",
        description="Create a new alert associated with a camera.",
        tags=["Alerts"]
    )
)
class AlertListCreateView(generics.ListCreateAPIView):
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]       

    def get_queryset(self):
        
        
        user = self.request.user
        print(user.company)
        queryset = Alert.objects.filter(camera__owner=user.company)

        # Filter by date range if provided
        from_date = self.request.query_params.get("fromDate")
        to_date = self.request.query_params.get("toDate")
        from_time = self.request.query_params.get("fromTime")
        to_time = self.request.query_params.get("toTime")       

        type = self.request.query_params.get("eventType")
        
        camera_id = self.request.query_params.get("camera_id")
        zone_id = self.request.query_params.get("zone_id") 

        search = self.request.query_params.get("search", None)

        if from_date and not from_time:
            from_time = "00:00:00"

        if to_date and not to_time:
            to_time = "23:59:59"   

        if from_date and from_time:
            try:
                from_dt = make_aware(datetime.strptime(f"{from_date} {from_time}", "%Y-%m-%d %H:%M:%S"))
                queryset = queryset.filter(timestamp__gte=from_dt)
            except ValueError:
                raise ParseError("Invalid 'fromDate' or 'fromTime' format. Expected format: YYYY-MM-DD HH:MM:SS")

        if to_date and to_time:
            try:
                to_dt = make_aware(datetime.strptime(f"{to_date} {to_time}", "%Y-%m-%d %H:%M:%S"))
                queryset = queryset.filter(timestamp__lte=to_dt)
            except ValueError:
                raise ParseError("Invalid 'toDate' or 'toTime' format. Expected format: YYYY-MM-DD HH:MM:SS")

        if not from_date and not to_date and from_time and to_time:
            try:
                from_t = datetime.strptime(from_time, "%H:%M:%S").time()
                to_t = datetime.strptime(to_time, "%H:%M:%S").time()
                queryset = queryset.annotate(time_only=Cast("timestamp", output_field=TimeField()))
                queryset = queryset.filter(time_only__gte=from_t, time_only__lte=to_t)
            except ValueError:
                raise ParseError("Invalid 'fromTime' or 'toTime' format. Expected format: HH:MM:SS")

        if type and type.lower() != "all_types":
            queryset = queryset.filter(usecase__usecasse__type=type)    

        if camera_id and camera_id.lower() != "all-cameras":            
            try:
                camera_uuid = uuid.UUID(camera_id)
                queryset = queryset.filter(camera=camera_uuid)
            except ValueError:
                queryset = queryset.none()    

        if zone_id and zone_id.lower() != "all-zones":
            try:
                zone_uuid = uuid.UUID(zone_id)
                queryset = queryset.filter(camera__assigned_zone_id=zone_uuid)
            except ValueError:
                queryset = queryset.none()        

        if search:
            queryset = queryset.filter(
                Q(usecase__usecasse__type__icontains=search) |               
                Q(camera__name__icontains=search) |
                Q(camera__location__icontains=search)
            )        

        return queryset.order_by("-timestamp")

    def perform_create(self, serializer):
        user = self.request.user
        # camera_id = serializer.validated_data.get('camera_id')
        # camera = Camera.objects.get(id=camera_id, owner=user.company)
        serializer.save(owner=user.company, resolved_by=user)

class AlertEventTypeListView(generics.ListAPIView):
    serializer_class = EventTypeNameSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    
    def get_queryset(self):    
        return AlertTypeMaster.objects.values('type').annotate(id=Min('id')).order_by('id')
    

class AlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Alert.objects.filter(camera__owner=user.company)

# class AlertEventTypeListView(generics.ListAPIView):    
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):

#         types =Alert.objects.values_list('type', flat=True).distinct().order_by('type')

#         return Response(types, status=status.HTTP_200_OK)
        


# Recording Management Views
class RecordingListCreateView(generics.ListCreateAPIView):
    serializer_class = RecordingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user        
        # queryset = Recording.objects.filter(owner=user.company)
        queryset = Recording.objects.all()
        # print(queryset)
        # Apply filters
        camera_id = self.request.query_params.get("cameraId")

        start_date = self.request.query_params.get("startDate")
        start_time = self.request.query_params.get("startTime")
        end_date = self.request.query_params.get("endDate")
        end_time = self.request.query_params.get("endTime")

        quality = self.request.query_params.get("quality")              
        print(type(quality), quality)
        for q in queryset:
            print(q.camera_id, type(q.camera_id))
        if camera_id and camera_id.lower() != "all":
            try:
                camera_uuid = uuid.UUID(camera_id)
                queryset = queryset.filter(camera_id=camera_uuid)
            except ValueError as e:
                print(e)
                queryset = queryset.none()  # Invalid UUID

        
        # Full datetime range (startDate+startTime to endDate+endTime)
        if start_date and end_date:
            try:
                s_time = datetime.strptime(start_time, "%H:%M:%S").time() if start_time else time(0, 0, 0)
                e_time = datetime.strptime(end_time, "%H:%M:%S").time() if end_time else time(23, 59, 59)

                start_dt = make_aware(datetime.combine(datetime.strptime(start_date, "%Y-%m-%d").date(), s_time))
                end_dt = make_aware(datetime.combine(datetime.strptime(end_date, "%Y-%m-%d").date(), e_time))

                queryset = queryset.filter(start_time__gte=start_dt, start_time__lte=end_dt)
            except ValueError as e:
                raise ParseError("Invalid date or time format. Expected YYYY-MM-DD and HH:MM:SS")

        # Only startDate (whole day)
        elif start_date:
            try:
                start_dt = make_aware(datetime.combine(datetime.strptime(start_date, "%Y-%m-%d").date(), time(0, 0, 0)))
                end_dt = make_aware(datetime.combine(datetime.strptime(start_date, "%Y-%m-%d").date(), time(23, 59, 59)))
                queryset = queryset.filter(start_time__gte=start_dt, start_time__lte=end_dt)
            except ValueError:
                raise ParseError("Invalid startDate format. Expected YYYY-MM-DD")

        # Only time filtering across all dates
        elif start_time and end_time:
            try:
                from_t = datetime.strptime(start_time, "%H:%M:%S").time()
                to_t = datetime.strptime(end_time, "%H:%M:%S").time()
                queryset = queryset.annotate(time_only=Cast("start_time", output_field=TimeField()))
                queryset = queryset.filter(time_only__gte=from_t, time_only__lte=to_t)
            except ValueError:
                raise ParseError("Invalid time format. Expected HH:MM:SS")

        if quality and quality != "all":
            print("here")
            queryset = queryset.filter(quality=quality)

        return queryset.order_by("-created_at")[:5]
    
    def perform_create(self, serializer):
        print('Received--- RECORDING POST')
        serializer.save()

"""
@auther: Mandar More
@date: 2024-07-09
@description:
Fetches `.mp4` recordings from S3 based on camera ID, date, and optional hour.
Inserts new entries into the database while avoiding duplicates.
Returns serialized recordings:
- If `hr` not provided → only `1.mp4` per hour.
- If `hr` + `show-all=show-all` → all `.mp4` files for that hour.
- Else → only `1.mp4` of the given hour.

"""
class BulkRecordingLoadAndListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BulkRecordingSerializer
    
    def list(self, request, *args, **kwargs):    
        camera_id = request.query_params.get("camera_id")       
        # Format: YYYY-MM-DD        
        date = request.query_params.get("date")  
        # Format: 00–23
        hr = request.query_params.get("hr")
        show_all = request.query_params.get("show-all")    
        zone_id = request.query_params.get("zone_id")
        
        if not camera_id:
            return Response(
                {"error": "camera_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
                
        try:
            camera_id = str(uuid.UUID(camera_id))
            camera = Camera.objects.get(id=camera_id)
        except (ValueError, ObjectDoesNotExist) as e:
            return Response(
                {"error": f"Invalid camera_id: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not camera_id or not date:
            return Response(
                {"error": "camera_id and date are required query parameters."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        prefix = f"{settings.S3_PREFIX.rstrip('/')}/{camera_id}/{date}/"
        if hr:
            prefix += f"{hr}/"

        try:
            s3 = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.REGION_NAME,
            )

            response = s3.list_objects_v2(Bucket=settings.S3_BUCKET, Prefix=prefix)

            if "Contents" not in response:
                return Response({
                    "camera_id": camera.id,
                    "camera_name": camera.name,
                    "camera_location": camera.location,
                    "date": date,
                    "recordings_inserted": 0,
                    "recordings": []
                }, status=status.HTTP_200_OK)

            grouped_files = defaultdict(list)
            
            for item in response["Contents"]:
                key = item["Key"]
                if key.endswith(".mp4"):
                    parts = key.split("/")
                    if len(parts) >= 5:
                        file_hr = parts[4]
                        url = os.path.join(settings.CDN_DOMAIN, key)
                        grouped_files[file_hr].append(url)

            for hour in grouped_files:
                grouped_files[hour] = sorted(
                    grouped_files[hour],
                    key=lambda url: int(url.split("/")[-1].split(".")[0])
                )
            
            bulk_objects = []
            for file_hr, urls in grouped_files.items():
                for url in urls:
                    file_path = url
                    filename = file_path.split("/")[-1]
                    try:
                        start_time = datetime.strptime(f"{date} {file_hr}", "%Y-%m-%d %H")
                    except ValueError:
                        continue

                    if not Recording.objects.filter(
                        camera=camera,
                        filename=filename,
                        start_time=start_time
                    ).exists():
                        end_time = start_time + timedelta(minutes=15)
                        bulk_objects.append(Recording(
                            camera=camera,
                            filename=filename,
                            file_path=file_path,
                            start_time=start_time,
                            end_time=end_time,
                            duration=timedelta(minutes=15),
                            has_motion=False,
                            has_audio=False,
                            thumbnail_path=None,
                            cloud_url=file_path,
                            is_archived=False,
                            checksum=None,
                            metadata={},
                            owner=getattr(camera, "owner", None)
                        ))
           
            Recording.objects.bulk_create(bulk_objects, ignore_conflicts=True)
            
            start_date = datetime.strptime(date, "%Y-%m-%d").date()
            if hr:
                recordings = Recording.objects.filter(
                    camera=camera,
                    start_time__date=start_date,
                    start_time__hour=int(hr)
                ).order_by("start_time")
            else:
                recordings = Recording.objects.filter(
                    camera=camera,
                    start_time__date=start_date
                ).order_by("start_time")

            if zone_id:
                try:
                    zone_uuid = uuid.UUID(zone_id)
                    recordings = recordings.filter(camera__assigned_zone_id=zone_uuid)
                except ValueError:
                    return Response(
                        {"error": "Invalid zone_id format."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
            if camera_id:
                try:
                    camera_uuid = uuid.UUID(camera_id)
                    recordings = recordings.filter(camera=camera_uuid)
                except ValueError:
                    return Response(
                        {"error": "Invalid camera_id format."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            page = self.paginate_queryset(recordings)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
            
                if not hr:
                    serializer_data = [r for r in serializer.data if r["filename"] == "1.mp4"]
                
                elif hr and show_all == "show-all":                
                    serializer_data = serializer.data
                
                else:
                    serializer_data = [r for r in serializer.data if r["filename"] == "1.mp4"]

                return self.get_paginated_response({
                    "camera_id": str(camera.id),
                    "camera_name": camera.name,
                    "camera_location": camera.location,
                    "date": date,
                    "recordings_inserted": len(bulk_objects),
                    "recordings": serializer_data
                })
            
            serializer = self.get_serializer(recordings, many=True)
            return Response({
                "camera_id": str(camera.id),
                "camera_name": camera.name,
                "camera_location": camera.location,
                "date": date,
                "recordings_inserted": len(bulk_objects),
                "recordings": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to fetch or store files: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecordingDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = RecordingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Recording.objects.filter(camera__owner=user.company)


class RecordingDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        try:
            recording = Recording.objects.get(pk=pk, camera__owner=user.company)

            if recording.file_path:
                response = FileResponse(
                    open(recording.file_path, "rb"), content_type="video/mp4"
                )
                response["Content-Disposition"] = (
                    f'attachment; filename="{recording.filename}"'
                )
                return response
            else:
                return Response(
                    {"error": "File not found"}, status=status.HTTP_404_NOT_FOUND
                )
        except Recording.DoesNotExist:
            raise Http404

"""
@author: Mandar More
@date: 2024-08-04
@description:
Fetches recordings for a specific camera and date, with hour and zone filters.
Returns serialized recordings:
- If `hr` not provided → only `1.mp4` per hour.
- If `hr` provided → all recordings for that hour.
- If `hr` + `show-all=show-all` → all recordings for that hour.
- If `hr` + `show-all` not provided → only `1.mp4` per hour.

"""
class RecordingListView(generics.ListAPIView):
    serializer_class = RecordingSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):    
        camera_id = request.query_params.get("camera_id")        
        date = request.query_params.get("date")  
        # Format: 00–23
        hr = request.query_params.get("hr")
        show_all = request.query_params.get("show-all")    
        zone_id = request.query_params.get("zone_id")
        
        if not camera_id or not date:
            return Response(
                {"error": "camera_id and date are required query parameters."},
                status=status.HTTP_400_BAD_REQUEST
            )      
                
        try:
            camera_id = str(uuid.UUID(camera_id))
            camera = Camera.objects.get(id=camera_id)
        except (ValueError, ObjectDoesNotExist) as e:
            return Response(
                {"error": f"Invalid camera_id: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )         
                
        try:
            start_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        

        recordings = Recording.objects.filter(
            camera=camera,
            start_time__date=start_date
        )

        # Hour filter
        if hr:
            try:
                hour_int = int(hr)
                if not (0 <= hour_int <= 23):
                    raise ValueError()
            except ValueError:
                return Response({"error": "Invalid hr value. Expect integer between 0 and 23."}, status=status.HTTP_400_BAD_REQUEST)
            recordings = recordings.filter(start_time__hour=hour_int)

        # Zone filter if provided
        if zone_id:
            try:
                zone_uuid = uuid.UUID(zone_id)
                recordings = recordings.filter(camera__assigned_zone_id=zone_uuid)
            except ValueError:
                return Response({"error": "Invalid zone_id format."}, status=status.HTTP_400_BAD_REQUEST)           
         

        recordings = recordings.order_by("start_time")
        

        page = self.paginate_queryset(recordings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
        
            if not hr:
                serializer_data = [r for r in serializer.data if r["filename"] == "1.mp4"]
            
            elif hr and show_all == "show-all":                
                serializer_data = serializer.data
            
            else:
                serializer_data = [r for r in serializer.data if r["filename"] == "1.mp4"]

            return self.get_paginated_response({
                "camera_id": str(camera.id),
                "camera_name": camera.name,
                "camera_location": camera.location,
                "date": date,                
                "recordings": serializer_data
            })
        
        serializer = self.get_serializer(recordings, many=True)
        return Response({
            "camera_id": str(camera.id),
            "camera_name": camera.name,
            "camera_location": camera.location,
            "date": date,           
            "recordings": serializer.data
        }, status=status.HTTP_200_OK)

   