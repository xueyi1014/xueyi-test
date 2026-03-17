from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
# 导入user APP的模型和序列化器
from .models import User
from .serializers import UserRegisterSerializer, UserInfoSerializer, ChangePasswordSerializer

class UserViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    authentication_classes = []

    # 注册接口 - 兼容带/和不带/的请求
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], authentication_classes=[])
    def register(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'msg': '注册成功'}, status=status.HTTP_201_CREATED)
        return Response({'msg': '注册失败', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    # 登录接口
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], authentication_classes=[])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                refresh = RefreshToken.for_user(user)
                return Response({
                    'token': str(refresh.access_token),
                    'refresh': str(refresh),
                    'username': user.username,
                    'role': user.role
                })
            else:
                return Response({'msg': '密码错误'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'msg': '用户不存在'}, status=status.HTTP_400_BAD_REQUEST)

    # 获取用户信息
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], authentication_classes=[JWTAuthentication])
    def info(self, request):
        serializer = UserInfoSerializer(request.user)
        return Response(serializer.data)

    # 更新个人信息
    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated], authentication_classes=[JWTAuthentication], url_path='update_profile')
    def update_profile(self, request):
        serializer = UserInfoSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 获取近期活动
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], authentication_classes=[JWTAuthentication])
    def recent_activities(self, request):
        from apps.activity.models import Activity, ActivityApply
        from django.utils import timezone
        from datetime import timedelta

        user = request.user
        if user.role != 'student':
            return Response([])

        # 获取最近 3 天内的待参与活动
        three_days_later = timezone.now() + timedelta(days=3)
        applies = ActivityApply.objects.filter(
            student=user,
            status='approved'
        ).select_related('batch__activity')

        recent_activities = []
        for apply in applies:
            activity = apply.batch.activity
            if activity.status == 'ongoing' and activity.start_time <= three_days_later:
                recent_activities.append({
                    'id': activity.id,
                    'name': activity.name,
                    'start_time': apply.batch.start_time,
                    'end_time': apply.batch.end_time,
                    'address': activity.address,
                    'checked_in': apply.check_in_time is not None
                })

        return Response(recent_activities[:5])

    # 获取教师统计数据
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], authentication_classes=[JWTAuthentication])
    def teacher_stats(self, request):
        from apps.activity.models import Activity, ActivityApply
        from apps.activity.models import AppealRecord
        from django.utils import timezone

        user = request.user
        if user.role != 'teacher':
            return Response({
                'publishedActivities': 0,
                'ongoingActivities': 0,
                'totalStudents': 0,
                'pendingAppeals': 0,
                'pendingApplies': 0
            })

        # 发布的活动数
        published_activities = Activity.objects.filter(organizer=user).count()
        
        # 进行中的活动数
        ongoing_activities = Activity.objects.filter(
            organizer=user,
            status='ongoing'
        ).count()
        
        # 总参与学生数（去重）
        total_students = ActivityApply.objects.filter(
            batch__activity__organizer=user
        ).values('student').distinct().count()
        
        # 待处理申诉数
        pending_appeals = AppealRecord.objects.filter(
            student__college=user.college,
            status='pending'
        ).count()
        
        # 待审核报名数
        pending_applies = ActivityApply.objects.filter(
            batch__activity__organizer=user,
            status='pending'
        ).count()

        return Response({
            'publishedActivities': published_activities,
            'ongoingActivities': ongoing_activities,
            'totalStudents': total_students,
            'pendingAppeals': pending_appeals,
            'pendingApplies': pending_applies
        })

    # 获取时长统计
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], authentication_classes=[JWTAuthentication])
    def hour_stats(self, request):
        from apps.activity.models import ActivityApply
        from django.db.models import Sum
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        user = request.user
        
        # 累计时长
        total_hours = user.total_hours
        
        # 已参与活动数
        completed_activities = ActivityApply.objects.filter(
            student=user,
            status='approved',
            check_out_time__isnull=False
        ).count()
        
        # 本月时长
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_hours = ActivityApply.objects.filter(
            student=user,
            status='approved',
            check_out_time__gte=month_start
        ).aggregate(total=Sum('hours'))['total'] or 0
        
        # 待审核时长
        pending_hours = ActivityApply.objects.filter(
            student=user,
            status='approved',
            check_out_time__isnull=True
        ).count()
        
        # 近6个月时长趋势
        monthly_stats = []
        for i in range(6):
            month_date = now - timedelta(days=30*i)
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            
            hours = ActivityApply.objects.filter(
                student=user,
                status='approved',
                check_out_time__gte=month_start,
                check_out_time__lte=month_end
            ).aggregate(total=Sum('hours'))['total'] or 0
            
            monthly_stats.append({
                'month': month_start.strftime('%Y-%m'),
                'hours': round(hours, 2)
            })
        
        monthly_stats.reverse()
        
        # 活动类型占比
        type_stats = ActivityApply.objects.filter(
            student=user,
            status='approved'
        ).values('batch__activity__type').annotate(
            count=Sum('hours')
        ).order_by('-count')
        
        type_data = []
        for stat in type_stats:
            type_data.append({
                'type': stat['batch__activity__type'],
                'hours': round(stat['count'], 2)
            })
        
        # 时长明细
        applies = ActivityApply.objects.filter(
            student=user,
            status='approved'
        ).select_related('batch__activity').order_by('-check_out_time')
        
        details = []
        for apply in applies:
            details.append({
                'activity_name': apply.batch.activity.name,
                'activity_type': apply.batch.activity.type,
                'start_time': apply.batch.start_time,
                'end_time': apply.batch.end_time,
                'hours': apply.hours,
                'status': 'completed' if apply.check_out_time else 'pending'
            })
        
        return Response({
            'total_hours': total_hours,
            'completed_activities': completed_activities,
            'month_hours': round(month_hours, 2),
            'pending_hours': pending_hours,
            'monthly_stats': monthly_stats,
            'type_stats': type_data,
            'details': details
        })

    # 获取违规记录
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], authentication_classes=[JWTAuthentication])
    def violations(self, request):
        from apps.activity.models import ViolationRecord, BlacklistAppeal
        
        user = request.user
        
        # 违规记录
        violations = ViolationRecord.objects.filter(
            student=user
        ).select_related('activity').order_by('-create_time')
        
        violation_list = []
        for v in violations:
            violation_list.append({
                'id': v.id,
                'type': v.violation_type,
                'description': v.description,
                'activity_name': v.activity.name if v.activity else '',
                'penalty_hours': v.penalty_hours,
                'create_time': v.create_time,
                'appealed': v.appeals.exists()
            })
        
        # 申诉记录
        appeals = BlacklistAppeal.objects.filter(
            student=user
        ).select_related('violation', 'reviewed_by').order_by('-create_time')
        
        appeal_list = []
        for appeal in appeals:
            appeal_list.append({
                'id': appeal.id,
                'violation_type': appeal.violation.violation_type,
                'violation_description': appeal.violation.description,
                'appeal_reason': appeal.appeal_reason,
                'status': appeal.status,
                'review_opinion': appeal.review_opinion,
                'review_time': appeal.review_time,
                'create_time': appeal.create_time
            })
        
        return Response({
            'violations': violation_list,
            'appeals': appeal_list,
            'violation_count': violations.count()
        })

    # 提交申诉
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], authentication_classes=[JWTAuthentication])
    def submit_appeal(self, request):
        from apps.activity.models import ViolationRecord, BlacklistAppeal
        
        violation_id = request.data.get('violation_id')
        appeal_reason = request.data.get('appeal_reason')
        evidence = request.data.get('evidence', '')
        
        if not violation_id or not appeal_reason:
            return Response({'msg': '参数不完整'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            violation = ViolationRecord.objects.get(id=violation_id, student=request.user)
            
            # 检查是否已申诉
            if violation.appeals.exists():
                return Response({'msg': '该违规记录已申诉'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 创建申诉
            appeal = BlacklistAppeal.objects.create(
                student=request.user,
                violation=violation,
                appeal_reason=appeal_reason,
                evidence=evidence,
                status='pending'
            )
            
            return Response({'msg': '申诉提交成功', 'appeal_id': appeal.id})
            
        except ViolationRecord.DoesNotExist:
            return Response({'msg': '违规记录不存在'}, status=status.HTTP_400_BAD_REQUEST)

    # 修改密码
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], authentication_classes=[JWTAuthentication])
    def changePwd(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            old_pwd = serializer.validated_data['oldPwd']
            new_pwd = serializer.validated_data['newPwd']
            user = request.user
            if user.check_password(old_pwd):
                user.set_password(new_pwd)
                user.save()
                return Response({'msg': '密码修改成功'})
            else:
                return Response({'msg': '原密码错误'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)