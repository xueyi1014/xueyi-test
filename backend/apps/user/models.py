from django.db import models
from django.contrib.auth.models import AbstractUser

# 自定义用户模型（必须命名为User，且继承AbstractUser）
class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', '学生'),
        ('teacher', '老师'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, verbose_name='身份', default='student')
    id_number = models.CharField(max_length=20, blank=True, null=True, verbose_name='学号/工号')
    phone = models.CharField(max_length=11, blank=True, null=True, verbose_name='手机号')
    total_hours = models.IntegerField(default=0, verbose_name='累计志愿时长')
    class_name = models.CharField(max_length=50, blank=True, null=True, verbose_name='负责班级')
    college = models.CharField(max_length=100, blank=True, null=True, verbose_name='学院')
    wechat = models.CharField(max_length=50, blank=True, null=True, verbose_name='微信号')
    email = models.EmailField(blank=True, null=True, verbose_name='邮箱')
    credit_level = models.IntegerField(default=5, verbose_name='信用等级')
    is_blacklisted = models.BooleanField(default=False, verbose_name='是否黑名单')
    blacklist_end_time = models.DateTimeField(null=True, blank=True, verbose_name='黑名单结束时间')
    violation_count = models.IntegerField(default=0, verbose_name='违规次数')
    completed_activities = models.IntegerField(default=0, verbose_name='已参与活动数')
    pending_activities = models.IntegerField(default=0, verbose_name='待参与活动数')

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
        db_table = 'user'  # 显式指定表名，避免冲突

    def __str__(self):
        return self.username