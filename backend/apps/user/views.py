from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import UserProfile

# 注册接口
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        student_id = request.data.get('student_id')
        phone = request.data.get('phone')

        if not all([username, password, student_id, phone]):
            return Response({'msg': '所有字段不能为空'}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({'msg': '用户名已存在'}, status=400)

        if UserProfile.objects.filter(student_id=student_id).exists():
            return Response({'msg': '学号已被注册'}, status=400)

        user = User.objects.create_user(username=username, password=password)
        UserProfile.objects.create(
            user=user,
            student_id=student_id,
            phone=phone
        )
        return Response({'msg': '注册成功'})

# 获取用户信息（个人中心）
class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.userprofile
        return Response({
            'username': request.user.username,
            'student_id': profile.student_id,
            'phone': profile.phone
        })