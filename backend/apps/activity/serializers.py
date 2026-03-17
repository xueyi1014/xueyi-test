from rest_framework import serializers
# 导入activity APP的模型
from .models import Activity, ActivityApply
# 关键修复：删除多余的backend前缀
from user.models import User  # 原代码如果有backend前缀也删掉

# 活动序列化器（老师发布/编辑）
class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ('id', 'name', 'type', 'time', 'address', 'quota', 'apply_count', 'creator')
        read_only_fields = ('id', 'apply_count', 'creator')

    def create(self, validated_data):
        # 自动关联创建人（当前登录的老师）
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)

# 活动列表序列化器（学生查看）
class StudentActivitySerializer(serializers.ModelSerializer):
    remaining_quota = serializers.SerializerMethodField()  # 剩余名额

    class Meta:
        model = Activity
        fields = ('id', 'name', 'type', 'time', 'address', 'quota', 'apply_count', 'remaining_quota')

    def get_remaining_quota(self, obj):
        return obj.quota - obj.apply_count

# 报名记录序列化器
class ActivityApplySerializer(serializers.ModelSerializer):
    activity_name = serializers.CharField(source='activity.name', read_only=True)
    student_name = serializers.CharField(source='student.username', read_only=True)

    class Meta:
        model = ActivityApply
        fields = ('id', 'activity', 'activity_name', 'student', 'student_name', 'apply_time', 'is_checkin', 'checkin_time', 'hours')
        read_only_fields = ('id', 'apply_time', 'student')

    def create(self, validated_data):
        # 自动关联报名学生（当前登录的学生）
        validated_data['student'] = self.context['request'].user
        return super().create(validated_data)