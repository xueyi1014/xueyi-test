from django.db import models
from apps.user.models import User
from apps.activity.models import Activity

class Registration(models.Model):
    STATUS_CHOICES = (
        (1, '待审核'),
        (2, '通过'),
        (3, '拒绝'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    is_sign = models.BooleanField(default=False)
    sign_time = models.DateTimeField(null=True, blank=True)
    service_time = models.FloatField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'registration'
        unique_together = ('user', 'activity')