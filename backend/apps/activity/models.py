from django.db import models
from apps.user.models import User

class Activity(models.Model):
    STATUS_CHOICES = (
        (1, '报名中'),
        (2, '进行中'),
        (3, '已结束'),
    )
    title = models.CharField(max_length=100)
    content = models.TextField()
    place = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    max_num = models.IntegerField()
    apply_end_time = models.DateTimeField()
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'activity'