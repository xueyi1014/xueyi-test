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