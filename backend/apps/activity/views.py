from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .models import Activity
from .serializers import ActivitySerializer

class ActivityList(ListCreateAPIView):
    queryset = Activity.objects.all().order_by('-created')
    serializer_class = ActivitySerializer

class ActivityDetail(RetrieveUpdateDestroyAPIView):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer