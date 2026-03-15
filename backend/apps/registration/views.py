from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Registration
from apps.activity.models import Activity
from django.utils import timezone

class Apply(APIView):
    def post(self, request):
        act_id = request.data.get('act_id')
        act = Activity.objects.get(id=act_id)
        if Registration.objects.filter(user=request.user, activity=act).exists():
            return Response({"msg": "已报名"})
        Registration.objects.create(user=request.user, activity=act)
        return Response({"msg": "报名成功"})

class Sign(APIView):
    def post(self, request):
        reg_id = request.data.get('reg_id')
        reg = Registration.objects.get(id=reg_id)
        reg.is_sign = True
        reg.sign_time = timezone.now()
        delta = reg.activity.end_time - reg.activity.start_time
        reg.service_time = delta.total_seconds() / 3600
        reg.save()
        return Response({"msg": "签到成功"})