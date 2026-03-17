from rest_framework import serializers
# 关键：导入user APP的User模型
from .models import User

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password', 'role', 'id_number', 'phone')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            role=validated_data['role'],
            id_number=validated_data.get('id_number'),
            phone=validated_data.get('phone')
        )
        return user

class UserInfoSerializer(serializers.ModelSerializer):
    idNumber = serializers.CharField(source='id_number', required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    totalHours = serializers.IntegerField(source='total_hours', read_only=True)
    classField = serializers.CharField(source='class_name', required=False, allow_blank=True, allow_null=True)
    class_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    college = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    wechat = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    completedActivities = serializers.SerializerMethodField()
    pendingActivities = serializers.SerializerMethodField()
    violationCount = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('username', 'role', 'idNumber', 'phone', 'totalHours', 'classField', 'class_name', 'college', 'wechat', 'email', 'completedActivities', 'pendingActivities', 'violationCount')
    
    def get_completedActivities(self, obj):
        from apps.activity.models import ActivityApply
        return ActivityApply.objects.filter(student=obj, status='approved', check_out_time__isnull=False).count()
    
    def get_pendingActivities(self, obj):
        from apps.activity.models import ActivityApply
        return ActivityApply.objects.filter(student=obj, status='approved', check_out_time__isnull=True).count()
    
    def get_violationCount(self, obj):
        from apps.activity.models import ViolationRecord
        return ViolationRecord.objects.filter(student=obj).count()

class ChangePasswordSerializer(serializers.Serializer):
    oldPwd = serializers.CharField(write_only=True, required=True)
    newPwd = serializers.CharField(write_only=True, required=True)