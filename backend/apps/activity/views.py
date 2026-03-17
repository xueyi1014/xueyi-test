from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
# 导入activity APP的模型和序列化器
from .models import Activity, ActivityApply
from .serializers import ActivitySerializer, StudentActivitySerializer, ActivityApplySerializer

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

    # 动态选择序列化器
    def get_serializer_class(self):
        if self.request.user.role == 'teacher':
            return ActivitySerializer
        return StudentActivitySerializer

    # 动态设置权限
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsTeacher()]
        elif self.action == 'apply':
            return [permissions.IsAuthenticated(), IsStudent()]
        return [permissions.IsAuthenticated()]

    # 老师只能看到自己创建的活动
    def get_queryset(self):
        if self.request.user.role == 'teacher':
            return Activity.objects.filter(creator=self.request.user)
        return Activity.objects.all()

    # 学生报名活动 - POST /api/activity/{id}/apply/
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated(), IsStudent()])
    def apply(self, request, pk=None):
        activity = self.get_object()
        # 检查名额
        if activity.apply_count >= activity.quota:
            return Response({'msg': '活动名额已满'}, status=status.HTTP_400_BAD_REQUEST)
        # 检查是否已报名
        if ActivityApply.objects.filter(activity=activity, student=request.user).exists():
            return Response({'msg': '已报名该活动'}, status=status.HTTP_400_BAD_REQUEST)
        # 创建报名记录
        apply = ActivityApply.objects.create(activity=activity, student=request.user)
        # 更新活动报名人数
        activity.apply_count += 1
        activity.save()
        return Response({'msg': '报名成功'}, status=status.HTTP_201_CREATED)

    # 学生查看自己的报名记录 - GET /api/activity/my_applies/
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated(), IsStudent()])
    def my_applies(self, request):
        applies = ActivityApply.objects.filter(student=request.user)
        serializer = ActivityApplySerializer(applies, many=True)
        return Response(serializer.data)

    # 老师查看活动报名列表 - GET /api/activity/{id}/applies/
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated(), IsTeacher()])
    def applies(self, request, pk=None):
        activity = self.get_object()
        applies = ActivityApply.objects.filter(activity=activity)
        serializer = ActivityApplySerializer(applies, many=True)
        return Response(serializer.data)