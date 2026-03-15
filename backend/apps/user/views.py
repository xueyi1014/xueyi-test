from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .serializers import RegisterSerializer, UserSerializer

class Register(APIView):
    permission_classes = [AllowAny]
    def post(self, req):
        ser = RegisterSerializer(data=req.data)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response({"msg":"注册成功"})

class UserInfo(APIView):
    def get(self, req):
        return Response(UserSerializer(req.user).data)