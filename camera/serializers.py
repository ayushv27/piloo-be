from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from core.models import Client, UserProfile, Camera, Zone, Alert, Recording, AlertTypeMaster


class ZoneSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(
        read_only=True
        # queryset=Client.objects.all(), required=False
    )
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Zone
        fields = [
            "id",
            "name",
            "type",
            "description",
            "coordinates",
            "is_active",
            "owner",
            "created_by",
        ]

    def validate(self, data):
        owner = self.context['request'].user.company
        name = data.get('name')

        if Zone.objects.filter(name=name, owner=owner).exists():
            raise ValidationError({'error': "Zone with this name already exists for your organization."})

        return data


class CameraSerializer(serializers.ModelSerializer):
    assignedZone = serializers.CharField(source="assigned_zone.name", required=False, read_only=True)
    assigned_zone = serializers.PrimaryKeyRelatedField(
        queryset=Zone.objects.all(), required=False
    )
    # recordingEnabled = serializers.BooleanField(source='recording_enabled')
    # retentionDays = serializers.IntegerField(source='retention_days')
    # rtspUrl = serializers.CharField(source='rtsp_url')
    owner = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(), required=False
    )    

    class Meta:
        model = Camera
        fields = [
            "id",
            "name",
            "location",
            "rtsp_url",
            "rtmp_url",
            "hls_url",
            "output_url",
            "status",
            "assigned_zone",
            "preset",
            "framerate",
            "video_bitrate",
            "audio_bitrate",
            "owner",
            "assignedZone",
            "sensitivity",
            "recording_enabled",
            "retention_days",
        ]  

class CameraNameSerializer(serializers.ModelSerializer):
    zone_id = serializers.UUIDField(source="assigned_zone.id", read_only=True)
    zone_camera_names = serializers.SerializerMethodField()

    class Meta:
        model = Camera
        fields = ["id", "name", "status", "zone_id", "zone_camera_names"]

    def get_zone_camera_names(self, obj):
        if obj.assigned_zone:
            cameras = Camera.objects.filter(assigned_zone=obj.assigned_zone)
            return [cam.name for cam in cameras]
        return []


class ZoneNameSerializer(serializers.ModelSerializer):

    class Meta:
        model = Zone
        fields = ["id", "name"]


class AlertSerializer(serializers.ModelSerializer):
    # camera = serializers.PrimaryKeyRelatedField(
    #     queryset=Camera.objects.all(), required=False
    # )

    # owner = serializers.PrimaryKeyRelatedField(
    #     queryset=Client.objects.all(), required=False
    # )
    # resolved_by = serializers.PrimaryKeyRelatedField(
    #     queryset=UserProfile.objects.all(), required=False
    # )
    # zone = serializers.PrimaryKeyRelatedField(
    #     queryset=Zone.objects.all(), required=False
    # )
    # camera = serializers.PrimaryKeyRelatedField(
    #     queryset=Camera.objects.all(), required=False
    # )

    camera = serializers.PrimaryKeyRelatedField(
        queryset=Camera.objects.all(), required=False
    )
    owner = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(), required=False
    )
    resolved_by = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(), required=False
    )
    zone = serializers.PrimaryKeyRelatedField(
        queryset=Zone.objects.all(), required=False
    )
    type_name = serializers.CharField(source="usecase.usecase.type", read_only=True)
    camera_name = serializers.CharField(source="camera.name", read_only=True)
    camera_location = serializers.CharField(source="camera.location", read_only=True)

    class Meta:
        model = Alert
        # fields = [
        #     "id",
        #     "type",
        #     "description",
        #     "camera",
        #     "timestamp",
        #     "status",
        #     "video_url",
        #     "owner",
        #     "resolved_by",
        #     "zone",
        # ]
        fields = [
            "id",
            "usecase",
            "type_name",
            "label",
            "zone",
            "timestamp",
            "status",
            "chunk_url",
            "frame_url",
            "confidence_score",
            "metadata",
            "resolved_by",
            "resolved_at",
            "owner",
            "camera",
            "camera_name",
            "camera_location",
        ]
        read_only_fields = ["resolved_by", "owner"]

class EventTypeNameSerializer(serializers.ModelSerializer):

    class Meta:
        model = AlertTypeMaster
        fields = ["id", "type"]

        
class AlertSSENotificationSerializer(serializers.ModelSerializer):
    camera_name = serializers.CharField(source="camera.name")

    class Meta:
        model = Alert
        fields = [
            "id",
            "timestamp",
            "usecase",
            "camera_name",
            "thumbnail_url",
            # "location",
            "status",
        ]


class RecordingSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(), required=False
    )
    camera_name = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    zone_name = serializers.SerializerMethodField()

    # cameraId = serializers.IntegerField(source="camera_id")
    # startTime = serializers.DateTimeField(source="start_time")
    # endTime = serializers.DateTimeField(source="end_time")
    # fileName = serializers.CharField(source="filename")
    # filePath = serializers.CharField(source="file_path")
    # fileSize = serializers.IntegerField(source="file_size")
    # hasMotion = serializers.BooleanField(source="has_motion")
    # hasAudio = serializers.BooleanField(source="has_audio")
    # thumbnailPath = serializers.CharField(source="thumbnail_path")
    # createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Recording
        fields = [
            "id",
            "camera",
            "camera_name",
            "location",
            "zone_name",
            "filename",
            "file_path",
            "start_time",
            "end_time",
            "duration",
            "file_size",
            "quality",
            # "hasMotion",
            # "hasAudio",
            # "thumbnailPath",
            "cloud_url",
            "owner",
            "created_at",
        ]

    def get_camera_name(self, obj):
        return obj.camera.name if obj.camera and obj.camera.name else None

    def get_location(self, obj):
        return obj.camera.location if obj.camera and obj.camera.location else None

    def get_zone_name(self, obj):
        if obj.camera and obj.camera.assigned_zone:
            return obj.camera.assigned_zone.name


class BulkRecordingSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Recording
        fields = [
            "id",
            "camera",
            "filename",
            "file_path",
            "start_time",
            "end_time",
            "duration",
            "file_size",
            "quality",
            "cloud_url",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]