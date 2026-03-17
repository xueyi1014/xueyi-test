from rest_framework import serializers
from .models import Activity, ActivityBatch, ActivityApply, CheckinRecord, ViolationRecord, ActivityFavorite, StudentUnavailableTime, BlacklistAppeal
from user.models import User

# 活动批次序列化器
class ActivityBatchSerializer(serializers.ModelSerializer):
    remaining_quota = serializers.SerializerMethodField()
    
    class Meta:
        model = ActivityBatch
        fields = ('id', 'batch_name', 'start_time', 'end_time', 'quota', 'apply_count', 'remaining_quota')
        read_only_fields = ('id', 'apply_count')
    
    def get_remaining_quota(self, obj):
        return obj.quota - obj.apply_count

# 活动序列化器（老师发布/编辑）
class ActivitySerializer(serializers.ModelSerializer):
    batches = ActivityBatchSerializer(many=True, read_only=True)
    total_quota = serializers.ReadOnlyField()
    total_apply_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Activity
        fields = ('id', 'name', 'type', 'organizer', 'address', 'description', 'training', 
                 'support', 'notice', 'status', 'creator', 'create_time', 'update_time',
                 'batches', 'total_quota', 'total_apply_count')
        read_only_fields = ('id', 'creator', 'create_time', 'update_time')

    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)

# 活动列表序列化器（学生查看）
class StudentActivitySerializer(serializers.ModelSerializer):
    total_quota = serializers.ReadOnlyField()
    total_apply_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Activity
        fields = ('id', 'name', 'type', 'organizer', 'address', 'status', 
                 'total_quota', 'total_apply_count')

# 报名记录序列化器
class ActivityApplySerializer(serializers.ModelSerializer):
    activity_name = serializers.CharField(source='batch.activity.name', read_only=True)
    batch_name = serializers.CharField(source='batch.batch_name', read_only=True)
    student_name = serializers.CharField(source='student.username', read_only=True)
    
    class Meta:
        model = ActivityApply
        fields = ('id', 'batch', 'activity_name', 'batch_name', 'student', 'student_name', 
                 'apply_time', 'status')
        read_only_fields = ('id', 'apply_time', 'student')

# 签到记录序列化器
class CheckinRecordSerializer(serializers.ModelSerializer):
    activity_name = serializers.CharField(source='apply.batch.activity.name', read_only=True)
    student_name = serializers.CharField(source='apply.student.username', read_only=True)
    
    class Meta:
        model = CheckinRecord
        fields = ('id', 'apply', 'activity_name', 'student_name', 'checkin_time', 
                 'checkin_code', 'hours')
        read_only_fields = ('id', 'checkin_time')

# 活动收藏序列化器
class ActivityFavoriteSerializer(serializers.ModelSerializer):
    activity_name = serializers.CharField(source='activity.name', read_only=True)
    activity_type = serializers.CharField(source='activity.type', read_only=True)
    activity_status = serializers.CharField(source='activity.status', read_only=True)
    
    class Meta:
        model = ActivityFavorite
        fields = ('id', 'student', 'activity', 'activity_name', 'activity_type', 'activity_status', 'create_time')
        read_only_fields = ('id', 'create_time')

# 学生不可用时间序列化器
class StudentUnavailableTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentUnavailableTime
        fields = ('id', 'student', 'start_time', 'end_time', 'reason', 'create_time')
        read_only_fields = ('id', 'create_time')

# 黑名单申诉序列化器
class BlacklistAppealSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.username', read_only=True)
    violation_description = serializers.CharField(source='violation.description', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True)
    
    class Meta:
        model = BlacklistAppeal
        fields = ('id', 'student', 'student_name', 'violation', 'violation_description', 
                 'appeal_reason', 'evidence', 'status', 'review_opinion', 'review_time', 
                 'reviewed_by', 'reviewed_by_name', 'create_time')
        read_only_fields = ('id', 'create_time')

# 违规记录序列化器
class ViolationRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.username', read_only=True)
    activity_name = serializers.CharField(source='activity.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ViolationRecord
        fields = ('id', 'student', 'student_name', 'activity', 'activity_name', 'violation_type', 
                 'description', 'penalty_hours', 'ban_days', 'ban_end_time', 'created_by', 
                 'created_by_name', 'create_time')
        read_only_fields = ('id', 'create_time')