from django.db import models
from users.models import User

# 活动模型
class Activity(models.Model):
    ACTIVITY_TYPE_CHOICES = (
        ('campus', '校园内'),
        ('community', '社区'),
        ('public', '公益'),
    )
    name = models.CharField(max_length=100, verbose_name='活动名称')
    type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES, verbose_name='活动类型')
    time = models.DateTimeField(verbose_name='活动时间')
    address = models.CharField(max_length=200, verbose_name='活动地点')
    quota = models.IntegerField(verbose_name='报名名额')
    apply_count = models.IntegerField(default=0, verbose_name='已报名人数')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_activities', verbose_name='创建人（老师）')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '志愿活动'
        verbose_name_plural = '志愿活动'

# 报名记录模型
class ActivityApply(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='applies', verbose_name='活动')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applied_activities', verbose_name='报名学生')
    apply_time = models.DateTimeField(auto_now_add=True, verbose_name='报名时间')
    is_checkin = models.BooleanField(default=False, verbose_name='是否签到')
    checkin_time = models.DateTimeField(null=True, blank=True, verbose_name='签到时间')
    hours = models.IntegerField(default=0, verbose_name='获得时长')

    class Meta:
        verbose_name = '活动报名'
        verbose_name_plural = '活动报名'
        unique_together = ('activity', 'student')  # 一个学生只能报名一个活动一次