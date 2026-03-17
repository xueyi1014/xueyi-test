from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.db import models
import random
import string
from .models import Activity, ActivityBatch, ActivityApply, CheckinRecord, ViolationRecord, ActivityFavorite, StudentUnavailableTime, BlacklistAppeal, ActivityRating, AttendanceRecord
from .serializers import (
    ActivitySerializer, StudentActivitySerializer, ActivityBatchSerializer,
    ActivityApplySerializer, CheckinRecordSerializer, ViolationRecordSerializer,
    ActivityFavoriteSerializer, StudentUnavailableTimeSerializer, BlacklistAppealSerializer
)

# 权限：仅老师可发布/管理活动
class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'teacher'

# 权限：仅学生可报名活动
class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'student'

class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()

    def get_serializer_class(self):
        # 确保 user 存在
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            if self.request.user.role == 'teacher':
                return ActivitySerializer
        return StudentActivitySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'publish', 'cancel', 'add_batch']:
            return [permissions.IsAuthenticated(), IsTeacher()]
        elif self.action in ['apply', 'my_applies', 'checkin']:
            return [permissions.IsAuthenticated(), IsStudent()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            if self.request.user.role == 'teacher':
                return Activity.objects.filter(creator=self.request.user)
        # 学生只能看到已发布的活动
        return Activity.objects.filter(status='published')

    def create(self, request, *args, **kwargs):
        print("=== 创建活动开始 ===")
        print("请求数据:", request.data)
        print("用户:", request.user)
        
        try:
            # 复制数据，避免修改原始数据
            data = request.data.copy()
            batches_data = data.pop('batches', [])
            
            # 使用序列化器创建活动
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            activity = serializer.instance
            
            # 创建批次
            for batch_data in batches_data:
                if batch_data.get('start_time') and batch_data.get('end_time'):
                    ActivityBatch.objects.create(
                        activity=activity,
                        batch_name=batch_data.get('batch_name'),
                        quota=batch_data.get('quota'),
                        start_time=batch_data.get('start_time'),
                        end_time=batch_data.get('end_time')
                    )
            
            # 重新获取序列化后的数据返回
            serializer = self.get_serializer(activity)
            headers = self.get_success_headers(serializer.data)
            print("创建成功")
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            
        except Exception as e:
            print("创建失败:", str(e))
            import traceback
            traceback.print_exc()
            raise

    def perform_create(self, serializer):
        # 设置活动创建人为当前用户，并直接设置为已发布状态
        serializer.save(creator=self.request.user, status='published')

    # 发布活动 - POST /api/activity/{id}/publish/
    def publish(self, request, pk=None):
        activity = self.get_object()
        if activity.status != 'draft':
            return Response({'msg': '只能发布草稿状态的活动'}, status=status.HTTP_400_BAD_REQUEST)
        activity.status = 'published'
        activity.save()
        return Response({'msg': '活动发布成功'})

    # 取消活动 - POST /api/activity/{id}/cancel/
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        activity = self.get_object()
        if activity.status not in ['draft', 'published']:
            return Response({'msg': '只能取消草稿或已发布状态的活动'}, status=status.HTTP_400_BAD_REQUEST)
        activity.status = 'cancelled'
        activity.save()
        return Response({'msg': '活动已取消'})

    # 添加批次 - POST /api/activity/{id}/add_batch/
    @action(detail=True, methods=['post'])
    def add_batch(self, request, pk=None):
        activity = self.get_object()
        serializer = ActivityBatchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(activity=activity)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 学生报名活动 - POST /api/activity/{id}/apply/
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        from django.db import transaction
        from django.db.models import F
        
        activity = self.get_object()
        batch_id = request.data.get('batch_id')
        
        if not batch_id:
            return Response({'msg': '请选择批次'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            batch = ActivityBatch.objects.get(id=batch_id, activity=activity)
        except ActivityBatch.DoesNotExist:
            return Response({'msg': '批次不存在'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查名额（使用乐观锁防止超报）
        if batch.apply_count >= batch.quota:
            return Response({'msg': '该批次名额已满'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查是否已报名
        if ActivityApply.objects.filter(batch=batch, student=request.user).exists():
            return Response({'msg': '已报名该批次'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查时间冲突
        conflicting_applies = ActivityApply.objects.filter(
            student=request.user,
            batch__start_time__lt=batch.end_time,
            batch__end_time__gt=batch.start_time,
            status='approved'
        )
        if conflicting_applies.exists():
            return Response({'msg': '该时间段已有其他活动安排'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 使用数据库事务和乐观锁处理并发报名
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                with transaction.atomic():
                    # 重新获取批次信息，确保数据最新
                    batch = ActivityBatch.objects.select_for_update().get(id=batch_id)
                    
                    # 再次检查名额（防止并发超报）
                    if batch.apply_count >= batch.quota:
                        return Response({'msg': '该批次名额已满'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    # 创建报名记录
                    apply = ActivityApply.objects.create(batch=batch, student=request.user)
                    
                    # 更新用户的待参与活动数
                    request.user.pending_activities += 1
                    request.user.save()
                    
                    # 使用原子操作更新报名人数
                    updated = ActivityBatch.objects.filter(
                        id=batch_id, 
                        apply_count__lt=F('quota')
                    ).update(apply_count=F('apply_count') + 1)
                    
                    if updated == 0:
                        # 名额已满，删除报名记录并回滚待参与活动数
                        apply.delete()
                        request.user.pending_activities -= 1
                        request.user.save()
                        return Response({'msg': '该批次名额已满'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    serializer = ActivityApplySerializer(apply)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                    
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    return Response({'msg': '报名失败，请稍后重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({'msg': '报名失败，请稍后重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 学生查看自己的报名记录 - GET /api/activity/my_applies/
    @action(detail=False, methods=['get'])
    def my_applies(self, request):
        applies = ActivityApply.objects.filter(student=request.user)
        serializer = ActivityApplySerializer(applies, many=True)
        return Response(serializer.data)

    # 取消报名 - DELETE /api/activity/cancel_apply/{id}/
    @action(detail=False, methods=['delete'], url_path='cancel_apply/(?P<apply_id>[^/.]+)')
    def cancel_apply(self, request, apply_id=None):
        from django.db import transaction
        
        try:
            with transaction.atomic():
                # 使用 select_for_update 获取行锁，防止竞态条件
                apply = ActivityApply.objects.select_for_update().get(id=apply_id, student=request.user)
                
                # 检查报名状态
                if apply.status != 'pending':
                    return Response({'msg': '只能取消待审核状态的报名'}, status=status.HTTP_400_BAD_REQUEST)
                
                # 检查是否已签到
                if hasattr(apply, 'checkin'):
                    return Response({'msg': '已签到，无法取消报名'}, status=status.HTTP_400_BAD_REQUEST)
                
                # 获取批次信息
                batch = apply.batch
                
                # 删除报名记录
                apply.delete()
                
                # 减少报名人数
                batch.apply_count = max(0, batch.apply_count - 1)
                batch.save()
                
                return Response({'msg': '取消报名成功'})
                
        except ActivityApply.DoesNotExist:
            return Response({'msg': '报名记录不存在'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'msg': '取消报名失败，请稍后重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 老师查看活动报名列表 - GET /api/activity/{id}/applies/
    @action(detail=True, methods=['get'])
    def applies(self, request, pk=None):
        activity = self.get_object()
        applies = ActivityApply.objects.filter(batch__activity=activity)
        serializer = ActivityApplySerializer(applies, many=True)
        return Response(serializer.data)

    # 审核报名 - POST /api/activity/{id}/review_apply/
    @action(detail=True, methods=['post'])
    def review_apply(self, request, pk=None):
        activity = self.get_object()
        apply_id = request.data.get('apply_id')
        action_type = request.data.get('action')  # 'approve' or 'reject'
        
        try:
            apply = ActivityApply.objects.get(id=apply_id, batch__activity=activity)
        except ActivityApply.DoesNotExist:
            return Response({'msg': '报名记录不存在'}, status=status.HTTP_400_BAD_REQUEST)
        
        if action_type == 'approve':
            apply.status = 'approved'
            msg = '报名已通过'
        elif action_type == 'reject':
            apply.status = 'rejected'
            msg = '报名已拒绝'
        else:
            return Response({'msg': '无效的操作类型'}, status=status.HTTP_400_BAD_REQUEST)
        
        apply.save()
        return Response({'msg': msg})

    # 签到 - POST /api/activity/{id}/checkin/
    @action(detail=True, methods=['post'])
    def checkin(self, request, pk=None):
        from django.db import transaction
        from django.utils import timezone
        
        activity = self.get_object()
        apply_id = request.data.get('apply_id')
        checkin_method = request.data.get('checkin_method', 'manual')  # qr_code, manual, batch
        checkin_location = request.data.get('checkin_location', '')
        
        if not apply_id:
            return Response({'msg': '请选择报名记录'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 使用事务和重试机制处理并发签到
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                with transaction.atomic():
                    # 获取报名记录（带锁）
                    apply = ActivityApply.objects.select_for_update().get(
                        id=apply_id, 
                        batch__activity=activity, 
                        student=request.user
                    )
                    
                    # 检查报名状态
                    if apply.status != 'approved':
                        return Response({'msg': '报名未通过审核，无法签到'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    # 检查是否已签到
                    if hasattr(apply, 'checkin'):
                        return Response({'msg': '已签到'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    # 检查签到时间是否在活动时间内（允许提前15分钟签到）
                    batch = apply.batch
                    now = timezone.now()
                    
                    if now < batch.start_time - timezone.timedelta(minutes=15):
                        return Response({'msg': '签到时间未到'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    if now > batch.end_time:
                        return Response({'msg': '活动已结束，无法签到'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    # 计算时长（小时）
                    duration_hours = (batch.end_time - batch.start_time).total_seconds() / 3600
                    
                    # 创建签到记录
                    checkin_record = CheckinRecord.objects.create(
                        apply=apply,
                        checkin_code=''.join(random.choices(string.ascii_uppercase + string.digits, k=6)),
                        hours=duration_hours
                    )
                    
                    # 创建考勤明细记录
                    attendance_record = AttendanceRecord.objects.create(
                        student=request.user,
                        activity=activity,
                        batch=batch,
                        apply=apply,
                        checkin_time=now,
                        actual_hours=duration_hours,
                        checkin_method=checkin_method,
                        checkin_location=checkin_location,
                        attendance_status='normal'
                    )
                    
                    # 更新学生总时长（使用原子操作）
                    from django.db.models import F
                    User.objects.filter(id=apply.student_id).update(
                        total_hours=F('total_hours') + duration_hours
                    )
                    
                    # 返回简化响应
                    return Response({
                        'msg': '签到成功',
                        'checkin_time': now.strftime('%Y-%m-%d %H:%M:%S'),
                        'activity_name': activity.name,
                        'batch_name': batch.batch_name,
                        'duration_hours': duration_hours
                    }, status=status.HTTP_201_CREATED)
                    
            except ActivityApply.DoesNotExist:
                return Response({'msg': '报名记录不存在'}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    return Response({'msg': '签到失败，请稍后重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({'msg': '签到失败，请稍后重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 签退 - POST /api/activity/{id}/checkout/
    @action(detail=True, methods=['post'])
    def checkout(self, request, pk=None):
        from django.db import transaction
        from django.utils import timezone
        
        activity = self.get_object()
        apply_id = request.data.get('apply_id')
        
        if not apply_id:
            return Response({'msg': '请选择报名记录'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # 获取报名记录（带锁）
                apply = ActivityApply.objects.select_for_update().get(
                    id=apply_id,
                    batch__activity=activity,
                    student=request.user
                )
                
                # 检查是否已签到
                if not hasattr(apply, 'checkin'):
                    return Response({'msg': '尚未签到，无法签退'}, status=status.HTTP_400_BAD_REQUEST)
                
                # 检查是否已签退
                if apply.check_out_time:
                    return Response({'msg': '已签退'}, status=status.HTTP_400_BAD_REQUEST)
                
                # 更新签到记录
                checkin_record = apply.checkin
                now = timezone.now()
                
                # 计算实际时长（小时）
                actual_hours = (now - checkin_record.checkin_time).total_seconds() / 3600
                
                # 更新签到记录
                checkin_record.checkout_time = now
                checkin_record.hours = actual_hours
                checkin_record.save()
                
                # 更新报名记录
                apply.check_out_time = now
                apply.hours = actual_hours
                apply.save()
                
                # 更新考勤记录
                try:
                    attendance_record = AttendanceRecord.objects.get(apply=apply)
                    attendance_record.checkout_time = now
                    attendance_record.actual_hours = actual_hours
                    attendance_record.save()
                except AttendanceRecord.DoesNotExist:
                    pass
                
                # 更新学生总时长（减去之前预估的时长，加上实际时长）
                from django.db.models import F
                User.objects.filter(id=apply.student_id).update(
                    total_hours=F('total_hours') - checkin_record.hours + actual_hours
                )
                
                return Response({
                    'msg': '签退成功',
                    'checkout_time': now.strftime('%Y-%m-%d %H:%M:%S'),
                    'actual_hours': actual_hours
                })
                
        except ActivityApply.DoesNotExist:
            return Response({'msg': '报名记录不存在'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'msg': '签退失败，请稍后重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # 批量签到 - POST /api/activity/{id}/batch_checkin/
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated(), IsTeacher()])
    def batch_checkin(self, request, pk=None):
        from django.db import transaction
        
        activity = self.get_object()
        apply_ids = request.data.get('apply_ids', [])
        
        if not apply_ids:
            return Response({'msg': '请选择要签到的学生'}, status=status.HTTP_400_BAD_REQUEST)
        
        success_count = 0
        failed_applies = []
        
        for apply_id in apply_ids:
            try:
                with transaction.atomic():
                    apply = ActivityApply.objects.select_for_update().get(
                        id=apply_id,
                        batch__activity=activity,
                        status='approved'
                    )
                    
                    if not hasattr(apply, 'checkin'):
                        # 创建签到记录和考勤记录
                        CheckinRecord.objects.create(
                            apply=apply,
                            checkin_code='BATCH',
                            hours=apply.batch.duration_hours
                        )
                        
                        AttendanceRecord.objects.create(
                            student=apply.student,
                            activity=activity,
                            batch=apply.batch,
                            apply=apply,
                            checkin_time=timezone.now(),
                            actual_hours=apply.batch.duration_hours,
                            checkin_method='batch',
                            checkin_location='集体签到',
                            attendance_status='normal'
                        )
                        
                        # 更新学生总时长（使用原子操作）
                        from django.db.models import F
                        User.objects.filter(id=apply.student_id).update(
                            total_hours=F('total_hours') + apply.batch.duration_hours
                        )
                        
                        success_count += 1
                        
            except Exception as e:
                failed_applies.append({'apply_id': apply_id, 'error': str(e)})
        
        return Response({
            'msg': f'批量签到完成，成功：{success_count}人，失败：{len(failed_applies)}人',
            'failed_applies': failed_applies
        })

    # 收藏活动 - POST /api/activity/{id}/favorite/
    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        activity = self.get_object()
        
        if ActivityFavorite.objects.filter(student=request.user, activity=activity).exists():
            return Response({'msg': '已收藏该活动'}, status=status.HTTP_400_BAD_REQUEST)
        
        favorite = ActivityFavorite.objects.create(student=request.user, activity=activity)
        serializer = ActivityFavoriteSerializer(favorite)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # 取消收藏 - POST /api/activity/{id}/unfavorite/
    @action(detail=True, methods=['post'])
    def unfavorite(self, request, pk=None):
        activity = self.get_object()
        
        try:
            favorite = ActivityFavorite.objects.get(student=request.user, activity=activity)
            favorite.delete()
            return Response({'msg': '取消收藏成功'})
        except ActivityFavorite.DoesNotExist:
            return Response({'msg': '未收藏该活动'}, status=status.HTTP_400_BAD_REQUEST)

    # 检查是否已收藏 - GET /api/activity/{id}/is_favorite/
    @action(detail=True, methods=['get'])
    def is_favorite(self, request, pk=None):
        activity = self.get_object()
        is_favorite = ActivityFavorite.objects.filter(student=request.user, activity=activity).exists()
        return Response({'is_favorite': is_favorite})

    # 获取我的收藏列表 - GET /api/activity/my_favorites/
    @action(detail=False, methods=['get'])
    def my_favorites(self, request):
        favorites = ActivityFavorite.objects.filter(student=request.user).select_related('activity')
        serializer = ActivityFavoriteSerializer(favorites, many=True)
        return Response(serializer.data)

    # 检查时间冲突 - POST /api/activity/{id}/check_conflict/
    @action(detail=True, methods=['post'])
    def check_conflict(self, request, pk=None):
        activity = self.get_object()
        batch_id = request.data.get('batch_id')
        
        if not batch_id:
            return Response({'msg': '请选择批次'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            batch = ActivityBatch.objects.get(id=batch_id, activity=activity)
        except ActivityBatch.DoesNotExist:
            return Response({'msg': '批次不存在'}, status=status.HTTP_400_BAD_REQUEST)
        
        conflicts = []
        
        # 检查已报名活动冲突
        conflicting_applies = ActivityApply.objects.filter(
            student=request.user,
            batch__start_time__lt=batch.end_time,
            batch__end_time__gt=batch.start_time,
            status='approved'
        )
        
        for apply in conflicting_applies:
            conflicts.append({
                'type': 'activity',
                'message': f'与已报名活动「{apply.batch.activity.name} - {apply.batch.batch_name}」时间冲突',
                'start_time': apply.batch.start_time,
                'end_time': apply.batch.end_time
            })
        
        # 检查个人不可用时间冲突
        conflicting_times = StudentUnavailableTime.objects.filter(
            student=request.user,
            start_time__lt=batch.end_time,
            end_time__gt=batch.start_time
        )
        
        for unavailable_time in conflicting_times:
            conflicts.append({
                'type': 'unavailable',
                'message': f'与个人不可用时间冲突：{unavailable_time.reason or "无说明"}',
                'start_time': unavailable_time.start_time,
                'end_time': unavailable_time.end_time
            })
        
        return Response({
            'has_conflict': len(conflicts) > 0,
            'conflicts': conflicts
        })

    # 活动精准筛选 - GET /api/activity/filter/
    @action(detail=False, methods=['get'])
    def filter_activities(self, request):
        from django.utils import timezone
        from datetime import timedelta
        
        # 获取筛选参数
        activity_type = request.query_params.get('type')
        campus = request.query_params.get('campus')
        duration = request.query_params.get('duration')
        time_period = request.query_params.get('time_period')
        threshold = request.query_params.get('threshold')
        status = request.query_params.get('status')
        is_urgent = request.query_params.get('is_urgent')
        
        # 构建查询条件
        queryset = Activity.objects.filter(status__in=['published', 'recruiting', 'in_progress'])
        
        if activity_type:
            queryset = queryset.filter(type=activity_type)
        
        if campus:
            queryset = queryset.filter(campus=campus)
        
        if duration:
            # 根据时长区间筛选
            if duration == '1h':
                queryset = queryset.filter(batches__duration_hours__lte=1)
            elif duration == '1-2h':
                queryset = queryset.filter(batches__duration_hours__gte=1, batches__duration_hours__lte=2)
            elif duration == '2h+':
                queryset = queryset.filter(batches__duration_hours__gt=2)
        
        if time_period:
            now = timezone.now()
            if time_period == 'weekend':
                # 筛选周末活动
                queryset = queryset.filter(batches__start_time__week_day__in=[1, 7])
            elif time_period == 'lunch':
                # 午休时段 11:30-13:30
                queryset = queryset.filter(batches__start_time__hour__gte=11, batches__start_time__hour__lt=14)
            elif time_period == 'evening':
                # 晚间时段 18:00后
                queryset = queryset.filter(batches__start_time__hour__gte=18)
        
        if threshold:
            queryset = queryset.filter(registration_threshold=threshold)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if is_urgent == 'true':
            queryset = queryset.filter(is_urgent=True)
        
        # 去重并排序
        queryset = queryset.distinct().order_by('-is_urgent', '-create_time')
        
        serializer = StudentActivitySerializer(queryset, many=True)
        return Response(serializer.data)

    # 智能推荐 - GET /api/activity/recommendations/
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        from django.utils import timezone
        from django.db.models import Count, Avg
        
        user = request.user
        recommendations = []
        
        # 1. 基于历史报名的推荐
        user_applies = ActivityApply.objects.filter(student=user, status='approved')
        if user_applies.exists():
            # 获取用户常报名的活动类型
            favorite_types = user_applies.values('batch__activity__type').annotate(
                count=Count('id')
            ).order_by('-count')[:3]
            
            for type_info in favorite_types:
                activity_type = type_info['batch__activity__type']
                similar_activities = Activity.objects.filter(
                    type=activity_type,
                    status__in=['published', 'recruiting'],
                    batches__start_time__gt=timezone.now()
                ).exclude(
                    batches__activityapply__student=user
                ).distinct().order_by('-avg_rating')[:5]
                
                for activity in similar_activities:
                    recommendations.append({
                        'activity': StudentActivitySerializer(activity).data,
                        'reason': f'基于您常参与的{activity.get_type_display()}活动推荐',
                        'priority': 1
                    })
        
        # 2. 基于专业适配的推荐
        user_college = user.college or ''
        if user_college:
            # 根据学院推荐相关活动
            college_keywords = {
                '计算机': ['机房维护', '线上志愿', '技术培训'],
                '教育': ['赛事协助', '支教', '讲座协助'],
                '体育': ['运动会', '体育赛事', '健身指导'],
                '艺术': ['文艺活动', '展览协助', '表演支持']
            }
            
            for keyword, activities_keywords in college_keywords.items():
                if keyword in user_college:
                    college_activities = Activity.objects.filter(
                        status__in=['published', 'recruiting'],
                        batches__start_time__gt=timezone.now()
                    ).filter(
                        models.Q(name__icontains=activities_keywords[0]) |
                        models.Q(description__icontains=activities_keywords[0])
                    ).exclude(
                        batches__activityapply__student=user
                    ).distinct().order_by('-avg_rating')[:3]
                    
                    for activity in college_activities:
                        recommendations.append({
                            'activity': StudentActivitySerializer(activity).data,
                            'reason': f'基于您的{user_college}专业背景推荐',
                            'priority': 2
                        })
        
        # 3. 热门活动推荐
        popular_activities = Activity.objects.filter(
            status__in=['published', 'recruiting'],
            batches__start_time__gt=timezone.now()
        ).annotate(
            apply_count=Count('batches__activityapply')
        ).order_by('-apply_count', '-avg_rating')[:5]
        
        for activity in popular_activities:
            recommendations.append({
                'activity': StudentActivitySerializer(activity).data,
                'reason': '当前热门活动，报名人数较多',
                'priority': 3
            })
        
        # 4. 紧急活动推荐
        urgent_activities = Activity.objects.filter(
            is_urgent=True,
            status__in=['published', 'recruiting'],
            batches__start_time__gt=timezone.now()
        ).exclude(
            batches__activityapply__student=user
        ).distinct().order_by('-create_time')[:3]
        
        for activity in urgent_activities:
            recommendations.append({
                'activity': StudentActivitySerializer(activity).data,
                'reason': '紧急招募，急需志愿者',
                'priority': 0  # 最高优先级
            })
        
        # 按优先级排序并去重
        seen_activities = set()
        unique_recommendations = []
        
        for rec in sorted(recommendations, key=lambda x: x['priority']):
            activity_id = rec['activity']['id']
            if activity_id not in seen_activities:
                seen_activities.add(activity_id)
                unique_recommendations.append(rec)
        
        return Response(unique_recommendations[:10])  # 返回前10个推荐

    # 紧急活动快速发布 - POST /api/activity/urgent/
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated(), IsTeacher()])
    def create_urgent(self, request):
        from django.utils import timezone
        
        # 获取紧急活动数据
        name = request.data.get('name')
        start_time = request.data.get('start_time')
        end_time = request.data.get('end_time')
        address = request.data.get('address')
        quota = request.data.get('quota')
        work_content = request.data.get('work_content')
        contact_info = request.data.get('contact_info')
        
        # 验证必填字段
        required_fields = ['name', 'start_time', 'end_time', 'address', 'quota', 'work_content', 'contact_info']
        for field in required_fields:
            if not request.data.get(field):
                return Response({'msg': f'请填写{field}'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证时间合理性
        try:
            start_time_dt = timezone.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_time_dt = timezone.datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            if start_time_dt <= timezone.now():
                return Response({'msg': '开始时间必须晚于当前时间'}, status=status.HTTP_400_BAD_REQUEST)
            
            if end_time_dt <= start_time_dt:
                return Response({'msg': '结束时间必须晚于开始时间'}, status=status.HTTP_400_BAD_REQUEST)
                
        except ValueError:
            return Response({'msg': '时间格式不正确'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建紧急活动
        activity = Activity.objects.create(
            name=name,
            type='emergency',
            organizer=request.user.username + '（紧急发布）',
            address=address,
            campus='松山湖校区',  # 默认校区
            description=work_content,
            notice=f'紧急活动，联系人：{contact_info}',
            status='published',
            is_urgent=True,
            registration_threshold='no_threshold',  # 紧急活动无需审核
            creator=request.user
        )
        
        # 创建批次
        batch = ActivityBatch.objects.create(
            activity=activity,
            batch_name='紧急批次',
            start_time=start_time_dt,
            end_time=end_time_dt,
            quota=int(quota),
            description=work_content
        )
        
        # 设置紧急活动过期时间（24小时后）
        activity.expire_time = timezone.now() + timezone.timedelta(hours=24)
        activity.save()
        
        # 发送紧急通知（这里简化实现，实际可以集成短信/邮件通知）
        self._send_urgent_notification(activity)
        
        serializer = ActivitySerializer(activity)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def _send_urgent_notification(self, activity):
        """发送紧急活动通知"""
        # 这里可以集成短信、邮件或推送通知
        # 简化实现：记录日志
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f'紧急活动发布：{activity.name}，开始时间：{activity.batches.first().start_time}')
        
        # 实际实现中可以：
        # 1. 向所有符合条件的志愿者发送站内消息
        # 2. 集成短信通知（需要短信服务商）
        # 3. 发送邮件通知
        # 4. 推送手机通知

class ViolationViewSet(viewsets.ModelViewSet):
    queryset = ViolationRecord.objects.all()
    serializer_class = ViolationRecordSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        # 设置封禁结束时间
        ban_days = serializer.validated_data.get('ban_days', 0)
        if ban_days > 0:
            from django.utils import timezone
            from datetime import timedelta
            ban_end_time = timezone.now() + timedelta(days=ban_days)
            serializer.save(created_by=self.request.user, ban_end_time=ban_end_time)
        else:
            serializer.save(created_by=self.request.user)
    
    # 学生查看自己的违规记录 - GET /api/violation/my_violations/
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated(), IsStudent()])
    def my_violations(self, request):
        violations = ViolationRecord.objects.filter(student=request.user)
        serializer = ViolationRecordSerializer(violations, many=True)
        return Response(serializer.data)

class BlacklistAppealViewSet(viewsets.ModelViewSet):
    queryset = BlacklistAppeal.objects.all()
    serializer_class = BlacklistAppealSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'my_appeals']:
            return [permissions.IsAuthenticated(), IsStudent()]
        return [permissions.IsAuthenticated(), IsTeacher()]
    
    def perform_create(self, serializer):
        serializer.save(student=self.request.user)
    
    # 学生提交申诉（3步简化流程）
    @action(detail=False, methods=['post'])
    def submit_appeal(self, request):
        from django.db import transaction
        
        violation_id = request.data.get('violation_id')
        appeal_reason = request.data.get('appeal_reason')
        evidence = request.data.get('evidence', '')
        
        if not violation_id:
            return Response({'msg': '请选择违规记录'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not appeal_reason:
            return Response({'msg': '请输入申诉理由'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 使用事务处理申诉提交
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                with transaction.atomic():
                    # 获取违规记录（带锁）
                    violation = ViolationRecord.objects.select_for_update().get(id=violation_id, student=request.user)
                    
                    # 检查是否已提交申诉
                    if BlacklistAppeal.objects.filter(violation=violation).exists():
                        return Response({'msg': '已提交过申诉'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    # 创建申诉记录
                    appeal = BlacklistAppeal.objects.create(
                        student=request.user,
                        violation=violation,
                        appeal_reason=appeal_reason,
                        evidence=evidence
                    )
                    
                    # 返回简化响应
                    return Response({
                        'msg': '申诉提交成功',
                        'appeal_id': appeal.id,
                        'violation_type': violation.violation_type,
                        'appeal_reason': appeal_reason,
                        'submit_time': appeal.create_time.strftime('%Y-%m-%d %H:%M:%S')
                    }, status=status.HTTP_201_CREATED)
                    
            except ViolationRecord.DoesNotExist:
                return Response({'msg': '违规记录不存在'}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    return Response({'msg': '申诉提交失败，请稍后重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({'msg': '申诉提交失败，请稍后重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # 学生查看自己的申诉记录
    @action(detail=False, methods=['get'])
    def my_appeals(self, request):
        appeals = BlacklistAppeal.objects.filter(student=request.user)
        serializer = BlacklistAppealSerializer(appeals, many=True)
        return Response(serializer.data)
    
    # 老师审核申诉
    @action(detail=True, methods=['post'])
    def review_appeal(self, request, pk=None):
        appeal = self.get_object()
        action = request.data.get('action')  # 'approve' or 'reject'
        review_opinion = request.data.get('review_opinion', '')
        
        from django.utils import timezone
        
        if action == 'approve':
            appeal.status = 'approved'
            # 解除封禁
            if appeal.violation.ban_days > 0:
                appeal.violation.ban_end_time = timezone.now()
                appeal.violation.save()
        elif action == 'reject':
            appeal.status = 'rejected'
        else:
            return Response({'msg': '无效的操作'}, status=status.HTTP_400_BAD_REQUEST)
        
        appeal.review_opinion = review_opinion
        appeal.review_time = timezone.now()
        appeal.reviewed_by = request.user
        appeal.save()
        
        return Response({'msg': '审核完成'})

class BatchViewSet(viewsets.ModelViewSet):
    queryset = ActivityBatch.objects.all()
    serializer_class = ActivityBatchSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    
    def get_queryset(self):
        return ActivityBatch.objects.filter(activity__creator=self.request.user)

# Excel导出视图
class ExportViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    
    # 导出志愿时长报表
    @action(detail=False, methods=['post'])
    def export_hours(self, request):
        import pandas as pd
        from django.http import HttpResponse
        from io import BytesIO
        
        # 获取筛选条件
        activity_id = request.data.get('activity_id')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        # 查询签到记录
        checkin_records = CheckinRecord.objects.select_related(
            'apply__student', 'apply__batch__activity'
        ).all()
        
        # 应用筛选条件
        if activity_id:
            checkin_records = checkin_records.filter(apply__batch__activity_id=activity_id)
        
        if start_date:
            checkin_records = checkin_records.filter(checkin_time__gte=start_date)
        
        if end_date:
            checkin_records = checkin_records.filter(checkin_time__lte=end_date)
        
        # 构建数据
        data = []
        for record in checkin_records:
            student = record.apply.student
            activity = record.apply.batch.activity
            batch = record.apply.batch
            
            data.append({
                '姓名': student.username,
                '学号': student.id_number or '',
                '学院': student.college or '',
                '班级': student.class_name or '',
                '活动名称': activity.name,
                '活动时间': f'{batch.start_time} - {batch.end_time}',
                '志愿时长': record.hours,
                '签到状态': '已签到',
                '签到时间': record.checkin_time,
                '备注': ''
            })
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 生成Excel文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='志愿时长报表', index=False)
        
        # 设置响应头
        response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        # 生成文件名
        activity_name = '全部活动'
        if activity_id:
            try:
                activity = Activity.objects.get(id=activity_id)
                activity_name = activity.name
            except Activity.DoesNotExist:
                pass
        
        filename = f'{activity_name}_志愿时长报表_{timezone.now().strftime("%Y%m%d")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response

# 活动评价视图
class RatingViewSet(viewsets.ModelViewSet):
    queryset = ActivityRating.objects.all()
    serializer_class = None  # 稍后创建序列化器
    
    def get_permissions(self):
        if self.action in ['create', 'my_ratings']:
            return [permissions.IsAuthenticated(), IsStudent()]
        return [permissions.IsAuthenticated(), IsTeacher()]
    
    # 学生提交评价（3步简化流程）
    @action(detail=False, methods=['post'])
    def submit_rating(self, request):
        from django.db import transaction
        from django.utils import timezone
        
        apply_id = request.data.get('apply_id')
        overall_rating = request.data.get('overall_rating')
        dimension_ratings = request.data.get('dimension_ratings', {})
        comment = request.data.get('comment', '')
        photos = request.data.get('photos', [])
        is_anonymous = request.data.get('is_anonymous', False)
        
        if not apply_id:
            return Response({'msg': '请选择报名记录'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not overall_rating:
            return Response({'msg': '请选择评分'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 使用事务处理评价提交
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                with transaction.atomic():
                    # 获取报名记录（带锁）
                    apply = ActivityApply.objects.select_for_update().get(id=apply_id, student=request.user)
                    
                    # 检查是否已完成活动
                    if not hasattr(apply, 'checkin') or not apply.checkin:
                        return Response({'msg': '活动未完成，无法评价'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    # 检查是否已评价
                    if ActivityRating.objects.filter(student=request.user, activity=apply.batch.activity).exists():
                        return Response({'msg': '已评价过该活动'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    # 检查评价时限（活动结束后24小时内）
                    activity_end_time = apply.batch.end_time
                    if timezone.now() > activity_end_time + timezone.timedelta(hours=24):
                        return Response({'msg': '评价时限已过'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    # 创建评价
                    rating = ActivityRating.objects.create(
                        student=request.user,
                        activity=apply.batch.activity,
                        apply=apply,
                        overall_rating=overall_rating,
                        dimension_ratings=dimension_ratings,
                        comment=comment,
                        photos=photos,
                        is_anonymous=is_anonymous
                    )
                    
                    # 更新活动平均评分
                    activity = apply.batch.activity
                    activity.rating_count = ActivityRating.objects.filter(activity=activity).count()
                    activity.avg_rating = ActivityRating.objects.filter(activity=activity).aggregate(
                        avg=Avg('overall_rating')
                    )['avg'] or 0
                    activity.save()
                    
                    # 返回简化响应
                    return Response({
                        'msg': '评价提交成功',
                        'rating_id': rating.id,
                        'activity_name': activity.name,
                        'overall_rating': overall_rating,
                        'submit_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    
            except ActivityApply.DoesNotExist:
                return Response({'msg': '报名记录不存在'}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    return Response({'msg': '评价提交失败，请稍后重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({'msg': '评价提交失败，请稍后重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # 学生查看我的评价
    @action(detail=False, methods=['get'])
    def my_ratings(self, request):
        ratings = ActivityRating.objects.filter(student=request.user)
        # 这里需要创建序列化器
        data = []
        for rating in ratings:
            data.append({
                'id': rating.id,
                'activity_name': rating.activity.name,
                'overall_rating': rating.overall_rating,
                'comment': rating.comment,
                'create_time': rating.create_time
            })
        return Response(data)
    
    # 老师查看活动评价
    @action(detail=False, methods=['get'])
    def activity_ratings(self, request):
        activity_id = request.query_params.get('activity_id')
        if not activity_id:
            return Response({'msg': '请选择活动'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            activity = Activity.objects.get(id=activity_id, creator=request.user)
        except Activity.DoesNotExist:
            return Response({'msg': '活动不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        ratings = ActivityRating.objects.filter(activity=activity)
        data = []
        for rating in ratings:
            data.append({
                'id': rating.id,
                'student_name': '匿名用户' if rating.is_anonymous else rating.student.username,
                'overall_rating': rating.overall_rating,
                'dimension_ratings': rating.dimension_ratings,
                'comment': rating.comment,
                'photos': rating.photos,
                'teacher_reply': rating.teacher_reply,
                'create_time': rating.create_time
            })
        return Response(data)
    
    # 老师回复评价
    @action(detail=True, methods=['post'])
    def reply_rating(self, request, pk=None):
        from django.utils import timezone
        
        rating = self.get_object()
        reply_content = request.data.get('reply_content', '')
        
        if not reply_content:
            return Response({'msg': '请输入回复内容'}, status=status.HTTP_400_BAD_REQUEST)
        
        rating.teacher_reply = reply_content
        rating.reply_time = timezone.now()
        rating.save()
        
        return Response({'msg': '回复成功'})

# 考勤明细视图
class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.all()
    serializer_class = None  # 稍后创建序列化器
    
    def get_permissions(self):
        if self.action in ['my_attendance']:
            return [permissions.IsAuthenticated(), IsStudent()]
        return [permissions.IsAuthenticated(), IsTeacher()]
    
    # 学生查看考勤明细
    @action(detail=False, methods=['get'])
    def my_attendance(self, request):
        attendance_records = AttendanceRecord.objects.filter(student=request.user)
        data = []
        for record in attendance_records:
            data.append({
                'id': record.id,
                'activity_name': record.activity.name,
                'batch_name': record.batch.batch_name,
                'checkin_time': record.checkin_time,
                'checkout_time': record.checkout_time,
                'actual_hours': record.actual_hours,
                'attendance_status': record.attendance_status,
                'abnormal_reason': record.abnormal_reason
            })
        return Response(data)
    
    # 老师查看考勤明细
    @action(detail=False, methods=['get'])
    def activity_attendance(self, request):
        activity_id = request.query_params.get('activity_id')
        status_filter = request.query_params.get('status')
        
        if not activity_id:
            return Response({'msg': '请选择活动'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            activity = Activity.objects.get(id=activity_id, creator=request.user)
        except Activity.DoesNotExist:
            return Response({'msg': '活动不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        attendance_records = AttendanceRecord.objects.filter(activity=activity)
        
        if status_filter:
            attendance_records = attendance_records.filter(attendance_status=status_filter)
        
        data = []
        for record in attendance_records:
            data.append({
                'id': record.id,
                'student_name': record.student.username,
                'student_id': record.student.id_number,
                'college': record.student.college,
                'class_name': record.student.class_name,
                'batch_name': record.batch.batch_name,
                'checkin_time': record.checkin_time,
                'checkout_time': record.checkout_time,
                'actual_hours': record.actual_hours,
                'checkin_method': record.checkin_method,
                'checkin_location': record.checkin_location,
                'attendance_status': record.attendance_status,
                'abnormal_reason': record.abnormal_reason
            })
        return Response(data)
    
    # 老师修改考勤状态
    @action(detail=True, methods=['post'])
    def modify_attendance(self, request, pk=None):
        from django.utils import timezone
        
        record = self.get_object()
        new_status = request.data.get('status')
        reason = request.data.get('reason', '')
        
        if not new_status:
            return Response({'msg': '请选择新的考勤状态'}, status=status.HTTP_400_BAD_REQUEST)
        
        record.attendance_status = new_status
        record.abnormal_reason = reason
        record.modified_by = request.user
        record.modification_reason = f'手动修改：{reason}'
        record.modification_time = timezone.now()
        record.save()
        
        return Response({'msg': '考勤状态修改成功'})

# 海报生成视图
class PosterViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    
    # 生成活动海报
    @action(detail=True, methods=['post'])
    def generate_poster(self, request, pk=None):
        from django.http import HttpResponse
        from io import BytesIO
        from PIL import Image, ImageDraw, ImageFont
        import qrcode
        
        try:
            activity = Activity.objects.get(id=pk)
        except Activity.DoesNotExist:
            return Response({'msg': '活动不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        # 选择海报模板（这里简化实现，实际可以设计3套模板）
        template_id = request.data.get('template_id', 1)
        
        # 创建海报图像
        width, height = 800, 1200
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # 加载字体（这里使用默认字体，实际可以加载自定义字体）
        try:
            title_font = ImageFont.truetype('arial.ttf', 40)
            content_font = ImageFont.truetype('arial.ttf', 20)
        except:
            title_font = ImageFont.load_default()
            content_font = ImageFont.load_default()
        
        # 绘制海报内容
        y_position = 50
        
        # 标题
        draw.text((width//2, y_position), activity.name, fill='black', font=title_font, anchor='mm')
        y_position += 80
        
        # 主办方
        draw.text((width//2, y_position), f'主办方：{activity.organizer}', fill='gray', font=content_font, anchor='mm')
        y_position += 60
        
        # 时间地点
        batch_info = activity.batches.first()
        if batch_info:
            time_text = f'时间：{batch_info.start_time.strftime("%Y-%m-%d %H:%M")} - {batch_info.end_time.strftime("%H:%M")}'
            draw.text((width//2, y_position), time_text, fill='black', font=content_font, anchor='mm')
            y_position += 40
        
        draw.text((width//2, y_position), f'地点：{activity.address}', fill='black', font=content_font, anchor='mm')
        y_position += 60
        
        # 人数
        draw.text((width//2, y_position), f'人数：{activity.total_quota}人', fill='black', font=content_font, anchor='mm')
        y_position += 60
        
        # 注意事项（截取前100字符）
        notice = activity.notice[:100] + '...' if len(activity.notice) > 100 else activity.notice
        draw.text((width//2, y_position), f'注意事项：{notice}', fill='red', font=content_font, anchor='mm')
        y_position += 100
        
        # 生成二维码
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr_url = f'http://localhost:5174/activity/{activity.id}'
        qr.add_data(qr_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color='black', back_color='white')
        
        # 将二维码添加到海报
        qr_position = (width//2 - qr_img.size[0]//2, y_position)
        image.paste(qr_img, qr_position)
        
        # 保存图像到字节流
        output = BytesIO()
        image.save(output, format='PNG')
        output.seek(0)
        
        # 设置响应头
        response = HttpResponse(output.getvalue(), content_type='image/png')
        filename = f'{activity.name}_海报_{template_id}.png'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response

# 统计分析视图
class StatisticsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    
    # 全院时长统计
    @action(detail=False, methods=['get'])
    def hours_stats(self, request):
        from django.db.models import Sum, Count, Q, Value
        from django.db.models.functions import Coalesce, Cast
        from django.utils import timezone
        from datetime import datetime, timedelta
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # 获取筛选条件
            month = request.query_params.get('month')
            year = request.query_params.get('year')
            
            logger.info(f"Hours stats request - month: {month}, year: {year}")
            
            # 构建查询
            queryset = ActivityApply.objects.filter(status='approved', check_out_time__isnull=False)
            
            if month:
                queryset = queryset.filter(check_out_time__month=month)
            
            if year:
                queryset = queryset.filter(check_out_time__year=year)
            
            logger.info(f"Queryset count: {queryset.count()}")
            
            # 按学院统计
            college_stats = []
            college_data = queryset.values('student__college').annotate(
                total_hours=Coalesce(Sum('hours', output_field=models.FloatField()), Cast(Value(0), models.FloatField())),
                student_count=Count('student', distinct=True),
                activity_count=Count('id')
            ).order_by('-total_hours')
            
            for item in college_data:
                college_stats.append({
                    'student__college': item.get('student__college') or '未知学院',
                    'total_hours': float(item.get('total_hours') or 0),
                    'student_count': item.get('student_count') or 0,
                    'activity_count': item.get('activity_count') or 0
                })
            
            # 按班级统计
            class_stats = []
            class_data = queryset.values('student__college', 'student__class_name').annotate(
                total_hours=Coalesce(Sum('hours', output_field=models.FloatField()), Cast(Value(0), models.FloatField())),
                student_count=Count('student', distinct=True),
                activity_count=Count('id')
            ).order_by('-total_hours')
            
            for item in class_data:
                class_stats.append({
                    'student__college': item.get('student__college') or '未知学院',
                    'student__class_name': item.get('student__class_name') or '未知班级',
                    'total_hours': float(item.get('total_hours') or 0),
                    'student_count': item.get('student_count') or 0,
                    'activity_count': item.get('activity_count') or 0
                })
            
            # 总时长趋势（近12个月）
            monthly_trend = []
            for i in range(12):
                month_date = timezone.now() - timedelta(days=30*i)
                month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
                
                hours = queryset.filter(
                    check_out_time__gte=month_start,
                    check_out_time__lte=month_end
                ).aggregate(total=Sum('hours', output_field=models.FloatField()))['total'] or 0
                
                monthly_trend.append({
                    'month': month_start.strftime('%Y-%m'),
                    'hours': round(float(hours), 2)
                })
            
            monthly_trend.reverse()
            
            # 活跃度排名（学生）
            student_ranking = []
            student_data = queryset.values('student__username', 'student__id_number', 'student__college', 'student__class_name').annotate(
                total_hours=Coalesce(Sum('hours', output_field=models.FloatField()), Cast(Value(0), models.FloatField())),
                activity_count=Count('id')
            ).order_by('-total_hours')[:20]
            
            for item in student_data:
                student_ranking.append({
                    'student__username': item.get('student__username') or '未知',
                    'student__id_number': item.get('student__id_number') or '',
                    'student__college': item.get('student__college') or '未知学院',
                    'student__class_name': item.get('student__class_name') or '未知班级',
                    'total_hours': float(item.get('total_hours') or 0),
                    'activity_count': item.get('activity_count') or 0
                })
            
            result = {
                'college_stats': college_stats,
                'class_stats': class_stats,
                'monthly_trend': monthly_trend,
                'student_ranking': student_ranking
            }
            
            logger.info(f"Hours stats result: {result}")
            
            return Response(result)
        except Exception as e:
            logger.error(f"Hours stats error: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # 活动参与率统计
    @action(detail=False, methods=['get'])
    def participation_stats(self, request):
        from django.db.models import Count, Q
        
        activities = Activity.objects.filter(creator=request.user)
        
        stats = []
        for activity in activities:
            total_quota = activity.total_quota
            apply_count = activity.total_apply_count
            checkin_count = ActivityApply.objects.filter(
                batch__activity=activity,
                check_in_time__isnull=False
            ).count()
            
            stats.append({
                'activity_id': activity.id,
                'activity_name': activity.name,
                'total_quota': total_quota,
                'apply_count': apply_count,
                'checkin_count': checkin_count,
                'apply_rate': round(apply_count / total_quota * 100, 2) if total_quota > 0 else 0,
                'checkin_rate': round(checkin_count / apply_count * 100, 2) if apply_count > 0 else 0,
                'status': activity.status
            })
        
        return Response(stats)
    
    # 违规统计
    @action(detail=False, methods=['get'])
    def violation_stats(self, request):
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta
        
        # 获取筛选条件
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        # 构建查询
        queryset = ViolationRecord.objects.all()
        
        if month:
            queryset = queryset.filter(create_time__month=month)
        
        if year:
            queryset = queryset.filter(create_time__year=year)
        
        # 按类型统计
        type_stats = queryset.values('violation_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # 按月份统计（近12个月）
        monthly_stats = []
        for i in range(12):
            month_date = timezone.now() - timedelta(days=30*i)
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            
            count = queryset.filter(
                create_time__gte=month_start,
                create_time__lte=month_end
            ).count()
            
            monthly_stats.append({
                'month': month_start.strftime('%Y-%m'),
                'count': count
            })
        
        monthly_stats.reverse()
        
        # 黑名单学生
        blacklisted_users = User.objects.filter(is_blacklisted=True)
        
        return Response({
            'type_stats': list(type_stats),
            'monthly_stats': monthly_stats,
            'blacklisted_count': blacklisted_users.count(),
            'total_violations': queryset.count()
        })

# 时长管理视图
class HoursManagementViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated(), IsTeacher()]
    
    # 查看活动学生时长
    @action(detail=False, methods=['get'])
    def activity_hours(self, request):
        activity_id = request.query_params.get('activity_id')
        
        if not activity_id:
            return Response({'msg': '请选择活动'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            activity = Activity.objects.get(id=activity_id, creator=request.user)
        except Activity.DoesNotExist:
            return Response({'msg': '活动不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        applies = ActivityApply.objects.filter(
            batch__activity=activity,
            status='approved'
        ).select_related('student', 'batch')
        
        data = []
        for apply in applies:
            data.append({
                'apply_id': apply.id,
                'student_name': apply.student.username,
                'student_id': apply.student.id_number,
                'college': apply.student.college,
                'class_name': apply.student.class_name,
                'batch_name': apply.batch.batch_name,
                'hours': apply.hours,
                'checkin_status': '已签到' if apply.check_in_time else '未签到'
            })
        
        return Response(data)
    
    # 修改学生时长
    @action(detail=False, methods=['post'])
    def update_hours(self, request):
        apply_id = request.data.get('apply_id')
        new_hours = request.data.get('hours')
        reason = request.data.get('reason', '')
        
        if not apply_id or new_hours is None:
            return Response({'msg': '参数不完整'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            apply = ActivityApply.objects.get(
                id=apply_id,
                batch__activity__creator=request.user
            )
            
            # 更新时长
            old_hours = apply.hours
            apply.hours = new_hours
            apply.save()
            
            # 更新签到记录
            if hasattr(apply, 'checkin'):
                apply.checkin.hours = new_hours
                apply.checkin.save()
            
            # 更新学生总时长
            from django.db.models import F
            User.objects.filter(id=apply.student_id).update(
                total_hours=F('total_hours') - old_hours + new_hours
            )
            
            return Response({'msg': '时长修改成功'})
            
        except ActivityApply.DoesNotExist:
            return Response({'msg': '报名记录不存在'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 批量录入时长
    @action(detail=False, methods=['post'])
    def batch_update_hours(self, request):
        from django.db import transaction
        from django.db.models import Sum, F, Case, When, IntegerField
        
        activity_id = request.data.get('activity_id')
        hours = request.data.get('hours')
        reason = request.data.get('reason', '')
        
        if not activity_id or hours is None:
            return Response({'msg': '参数不完整'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                activity = Activity.objects.select_for_update().get(id=activity_id, creator=request.user)
                applies = ActivityApply.objects.filter(
                    batch__activity=activity,
                    status='approved'
                ).select_related('student', 'checkin')
                
                if not applies.exists():
                    return Response({'msg': '没有找到符合条件的报名记录'}, status=status.HTTP_400_BAD_REQUEST)
                
                # 计算每个学生的时长差值
                student_hours_diff = {}
                for apply in applies:
                    student_id = apply.student_id
                    old_hours = apply.hours
                    if student_id not in student_hours_diff:
                        student_hours_diff[student_id] = 0
                    student_hours_diff[student_id] += (hours - old_hours)
                
                # 批量更新ActivityApply的hours
                updated_applies = applies.update(hours=hours)
                
                # 批量更新CheckinRecord的hours
                CheckinRecord.objects.filter(
                    apply__batch__activity=activity,
                    apply__status='approved'
                ).update(hours=hours)
                
                # 批量更新学生的总时长
                for student_id, hours_diff in student_hours_diff.items():
                    User.objects.filter(id=student_id).update(
                        total_hours=F('total_hours') + hours_diff
                    )
                
                return Response({
                    'msg': f'批量更新成功，共更新{updated_applies}名学生'
                })
                
        except Activity.DoesNotExist:
            return Response({'msg': '活动不存在'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'msg': f'批量更新失败：{str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 报名管理视图
class ApplicationManagementViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    
    # 查看活动报名列表
    @action(detail=False, methods=['get'])
    def activity_applies(self, request):
        activity_id = request.query_params.get('activity_id')
        status_filter = request.query_params.get('status')
        college_filter = request.query_params.get('college')
        credit_filter = request.query_params.get('credit')
        
        # 如果没有选择具体活动，则显示该教师创建的所有活动的报名
        if activity_id:
            try:
                activity = Activity.objects.get(id=activity_id, creator=request.user)
                applies = ActivityApply.objects.filter(batch__activity=activity)
            except Activity.DoesNotExist:
                return Response({'msg': '活动不存在'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # 显示该教师创建的所有活动的报名
            applies = ActivityApply.objects.filter(batch__activity__creator=request.user)
        
        # 状态筛选
        if status_filter:
            applies = applies.filter(status=status_filter)
        
        # 学院筛选
        if college_filter:
            applies = applies.filter(student__college=college_filter)
        
        # 信用等级筛选
        if credit_filter:
            if credit_filter == 'blacklist':
                applies = applies.filter(student__is_blacklisted=True)
            elif credit_filter == 'low_credit':
                applies = applies.filter(student__credit_level__lt=3)
            elif credit_filter == 'high_credit':
                applies = applies.filter(student__credit_level__gte=3)
        
        data = []
        for apply in applies.select_related('student', 'batch'):
            # 检查学生是否有多次违约
            violation_count = ViolationRecord.objects.filter(student=apply.student).count()
            
            data.append({
                'apply_id': apply.id,
                'student_name': apply.student.username,
                'student_id': apply.student.id_number,
                'college': apply.student.college,
                'class_name': apply.student.class_name,
                'phone': apply.student.phone,
                'batch_name': apply.batch.batch_name,
                'apply_time': apply.apply_time,
                'status': apply.status,
                'credit_level': apply.student.credit_level,
                'is_blacklisted': apply.student.is_blacklisted,
                'violation_count': violation_count
            })
        
        return Response(data)
    
    # 批量审核报名
    @action(detail=False, methods=['post'])
    def batch_review(self, request):
        from django.db import transaction
        
        apply_ids = request.data.get('apply_ids', [])
        action_type = request.data.get('action')  # 'approve' or 'reject'
        
        if not apply_ids or not action_type:
            return Response({'msg': '参数不完整'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                applies = ActivityApply.objects.filter(
                    id__in=apply_ids,
                    batch__activity__creator=request.user
                )
                
                updated_count = 0
                for apply in applies:
                    old_status = apply.status
                    
                    if action_type == 'approve':
                        apply.status = 'approved'
                        # 如果是从待审核状态变为已通过，更新学生待参与活动数
                        if old_status == 'pending':
                            apply.student.pending_activities += 1
                            apply.student.save()
                    elif action_type == 'reject':
                        apply.status = 'rejected'
                        # 如果是从待审核状态变为已拒绝，不更新待参与活动数
                        # 如果是从已通过状态变为已拒绝，需要减少待参与活动数
                        if old_status == 'approved':
                            apply.student.pending_activities = max(0, apply.student.pending_activities - 1)
                            apply.student.save()
                    
                    apply.save()
                    updated_count += 1
                
                return Response({
                    'msg': f'批量审核完成，共处理{updated_count}条记录'
                })
                
        except Exception as e:
            return Response({'msg': '批量审核失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # 导出报名名单
    @action(detail=False, methods=['post'])
    def export_applies(self, request):
        import pandas as pd
        from django.http import HttpResponse
        from io import BytesIO
        
        activity_id = request.data.get('activity_id')
        
        if not activity_id:
            return Response({'msg': '请选择活动'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            activity = Activity.objects.get(id=activity_id, creator=request.user)
        except Activity.DoesNotExist:
            return Response({'msg': '活动不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        applies = ActivityApply.objects.filter(
            batch__activity=activity
        ).select_related('student', 'batch')
        
        data = []
        for apply in applies:
            data.append({
                '学号': apply.student.id_number or '',
                '姓名': apply.student.username,
                '学院': apply.student.college or '',
                '班级': apply.student.class_name or '',
                '手机号': apply.student.phone or '',
                '报名批次': apply.batch.batch_name,
                '报名时间': apply.apply_time.strftime('%Y-%m-%d %H:%M:%S'),
                '状态': apply.status
            })
        
        df = pd.DataFrame(data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='报名名单', index=False)
        
        response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = f'{activity.name}_报名名单_{timezone.now().strftime("%Y%m%d")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response

# 违规申诉处理视图
class AppealManagementViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    
    # 查看所有申诉
    @action(detail=False, methods=['get'])
    def all_appeals(self, request):
        try:
            status_filter = request.query_params.get('status')
            
            appeals = BlacklistAppeal.objects.all().select_related(
                'student', 'violation', 'reviewed_by'
            ).order_by('-create_time')
            
            if status_filter:
                appeals = appeals.filter(status=status_filter)
            
            data = []
            for appeal in appeals:
                violation_data = {
                    'appeal_id': appeal.id,
                    'student_name': appeal.student.username if appeal.student else '',
                    'student_id': appeal.student.id_number if appeal.student else '',
                    'appeal_reason': appeal.appeal_reason or '',
                    'evidence': appeal.evidence or '',
                    'status': appeal.status or '',
                    'review_opinion': appeal.review_opinion or '',
                    'review_time': appeal.review_time,
                    'reviewed_by': appeal.reviewed_by.username if appeal.reviewed_by else '',
                    'create_time': appeal.create_time
                }
                
                # 只有当 violation 存在时才添加违规信息
                if appeal.violation:
                    violation_data['violation_type'] = appeal.violation.violation_type or ''
                    violation_data['violation_description'] = appeal.violation.description or ''
                    violation_data['penalty_hours'] = appeal.violation.penalty_hours or 0
                    violation_data['violation_create_time'] = appeal.violation.create_time
                else:
                    violation_data['violation_type'] = ''
                    violation_data['violation_description'] = ''
                    violation_data['penalty_hours'] = 0
                    violation_data['violation_create_time'] = None
                
                data.append(violation_data)
            
            return Response(data)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in all_appeals: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # 审核申诉
    @action(detail=False, methods=['post'])
    def review_appeal(self, request):
        appeal_id = request.data.get('appeal_id')
        action_type = request.data.get('action')  # 'approve' or 'reject'
        review_opinion = request.data.get('review_opinion', '')
        
        if not appeal_id or not action_type:
            return Response({'msg': '参数不完整'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            appeal = BlacklistAppeal.objects.get(id=appeal_id)
            
            if appeal.status != 'pending':
                return Response({'msg': '该申诉已处理'}, status=status.HTTP_400_BAD_REQUEST)
            
            if action_type == 'approve':
                appeal.status = 'approved'
                # 如果申诉通过，移除违规记录的影响
                violation = appeal.violation
                student = violation.student
                
                # 恢复扣除的时长（使用原子操作）
                if violation.penalty_hours > 0:
                    from django.db.models import F
                    User.objects.filter(id=student.id).update(
                        total_hours=F('total_hours') + violation.penalty_hours,
                        violation_count=F('violation_count') - 1
                    )
                
            elif action_type == 'reject':
                appeal.status = 'rejected'
            
            appeal.review_opinion = review_opinion
            appeal.review_time = timezone.now()
            appeal.reviewed_by = request.user
            appeal.save()
            
            return Response({'msg': '申诉审核完成'})
            
        except BlacklistAppeal.DoesNotExist:
            return Response({'msg': '申诉记录不存在'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 创建违规记录
    @action(detail=False, methods=['post'])
    def create_violation(self, request):
        from django.db import transaction
        
        student_id = request.data.get('student_id')
        activity_id = request.data.get('activity_id')
        violation_type = request.data.get('violation_type')
        description = request.data.get('description')
        penalty_hours = request.data.get('penalty_hours', 0)
        ban_days = request.data.get('ban_days', 0)
        
        if not all([student_id, activity_id, violation_type, description]):
            return Response({'msg': '参数不完整'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                student = User.objects.get(id=student_id)
                activity = Activity.objects.get(id=activity_id, creator=request.user)
                
                # 创建违规记录
                violation = ViolationRecord.objects.create(
                    student=student,
                    activity=activity,
                    violation_type=violation_type,
                    description=description,
                    penalty_hours=penalty_hours,
                    ban_days=ban_days,
                    created_by=request.user
                )
                
                # 更新学生信息（使用原子操作）
                from django.db.models import F, Case, When
                User.objects.filter(id=student_id).update(
                    violation_count=F('violation_count') + 1,
                    total_hours=Case(
                        When(total_hours__gte=penalty_hours, then=F('total_hours') - penalty_hours),
                        default=0,
                        output_field=models.IntegerField()
                    )
                )
                
                # 设置黑名单
                if ban_days > 0:
                    User.objects.filter(id=student_id).update(
                        is_blacklisted=True,
                        blacklist_end_time=violation.ban_end_time
                    )
                
                return Response({'msg': '违规记录创建成功', 'violation_id': violation.id})
                
        except User.DoesNotExist:
            return Response({'msg': '学生不存在'}, status=status.HTTP_400_BAD_REQUEST)
        except Activity.DoesNotExist:
            return Response({'msg': '活动不存在'}, status=status.HTTP_400_BAD_REQUEST)