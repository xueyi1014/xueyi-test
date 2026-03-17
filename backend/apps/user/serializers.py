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
    idNumber = serializers.CharField(source='id_number', read_only=True)
    phone = serializers.CharField(allow_blank=True, allow_null=True)
    totalHours = serializers.IntegerField(source='total_hours', read_only=True)
    classField = serializers.CharField(source='class_name', read_only=True, allow_blank=True, allow_null=True)
    
    class Meta:
        model = User
        fields = ('username', 'role', 'idNumber', 'phone', 'totalHours', 'classField')

class ChangePasswordSerializer(serializers.Serializer):
    oldPwd = serializers.CharField(write_only=True, required=True)
    newPwd = serializers.CharField(write_only=True, required=True)