from rest_framework import serializers
from  core.models import AlertTypeMaster

class AlertTypeMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertTypeMaster
        fields = ["id", "type", "name"]