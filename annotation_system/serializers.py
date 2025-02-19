from rest_framework import serializers
from .models import File, Annotation, AnnotationHistory
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class FileSerializer(serializers.ModelSerializer):
    annotation_count = serializers.IntegerField(read_only=True, default=0)
    progress = serializers.FloatField(read_only=True, default=0)
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    
    class Meta:
        model = File
        fields = '__all__'
        read_only_fields = [
            'uploaded_by', 'uploaded_at', 'page_count', 
            'file_size', 'status', 'checksum', 'progress'
        ]

class AnnotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Annotation
        fields = [
            'id',
            'file',
            'json_content',
            'version',
            'created_at',
            'updated_at',
            'verification_status',
            'comment'
        ]
    
    def to_representation(self, instance):
        # 获取基础字段
        data = {
            'id': instance.id,
            'file_id': instance.file_id,
            'version': instance.version,
            'created_at': instance.created_at.isoformat(),
            'updated_at': instance.updated_at.isoformat(),
            'verification_status': instance.verification_status,
            'comment': instance.comment or '',
            'data': instance.order_json_content()  # JSON 内容放在 data 字段中
        }
        return data

class AnnotationHistorySerializer(serializers.ModelSerializer):
    modified_by_name = serializers.CharField(source='modified_by.username', read_only=True)
    
    class Meta:
        model = AnnotationHistory
        fields = [
            'id',
            'version',
            'change_type',
            'change_description',
            'modified_by_name',
            'modified_at',
            'verification_status'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # 格式化时间
        data['modified_at'] = instance.modified_at.isoformat()
        return data 