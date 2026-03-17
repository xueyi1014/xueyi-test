from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from user.models import User

# 活动批次模型
class ActivityBatch(models.Model):
    activity = models.ForeignKey('Activity', on_delete=models.CASCADE, related_name='batches', verbose_name='所属活动')
    batch_name = models.CharField(max_length=50, verbose_name='批次名称')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(verbose_name='结束时间')
    quota = models.IntegerField(validators=[MinValueValidator(1)], verbose_name='批次名额')
    apply_count = models.IntegerField(default=0, verbose_name='已报名人数')
    
    class Meta:
        verbose_name = '活动批次'
        verbose_name_plural = '活动批次'
        ordering = ['start_time']

# 活动模型
class Activity(models.Model):
    TYPE_CHOICES = (
        ('campus', '校园服务'),
        ('community', '社区服务'),
        ('environment', '环保活动'),
        ('competition', '赛事协助'),
        ('emergency', '应急服务'),
        ('other', '其他'),
    )
    
    STATUS_CHOICES = (
        ('draft', '草稿'),
        ('published', '已发布'),
        ('cancelled', '已取消'),
        ('ended', '已结束'),
        ('full', '已报满'),
        ('recruiting', '招募中'),
        ('in_progress', '进行中'),
    )
    
    # 基础信息
    name = models.CharField(max_length=100, verbose_name='活动名称', default='未命名活动')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='活动类型', default='campus')
    organizer = models.CharField(max_length=100, verbose_name='主办方', default='未知主办方')
    address = models.CharField(max_length=200, verbose_name='活动地点', default='未知地点')
    campus = models.CharField(max_length=50, default='松山湖校区', verbose_name='校区')
    area = models.CharField(max_length=100, blank=True, verbose_name='具体区域')
    
    # 活动详情
    description = models.TextField(verbose_name='工作内容', default='暂无描述')
    training = models.TextField(blank=True, verbose_name='培训说明')
    support = models.TextField(blank=True, verbose_name='活动保障')
    notice = models.TextField(blank=True, verbose_name='注意事项')
    
    # 状态管理
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='活动状态')
    is_urgent = models.BooleanField(default=False, verbose_name='紧急活动')
    registration_threshold = models.CharField(max_length=20, default='no_threshold', choices=(
        ('no_threshold', '无门槛'),
        ('need_approval', '需审核'),
        ('high_priority', '高等级志愿者优先'),
    ), verbose_name='报名门槛')
    
    # 时间管理
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_activities', verbose_name='创建人')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    expire_time = models.DateTimeField(null=True, blank=True, verbose_name='过期时间')
    
    # 评价统计
    avg_rating = models.FloatField(default=0, verbose_name='平均评分')
    rating_count = models.IntegerField(default=0, verbose_name='评价数量')

    class Meta:
        verbose_name = '志愿活动'
        verbose_name_plural = '志愿活动'
        ordering = ['-create_time']
        indexes = [
            models.Index(fields=['type', 'status']),
            models.Index(fields=['campus', 'status']),
            models.Index(fields=['is_urgent', 'status']),
        ]

    def __str__(self):
        return self.name

    @property
    def total_quota(self):
        return sum(batch.quota for batch in self.batches.all())

    @property
    def total_apply_count(self):
        return ActivityApply.objects.filter(batch__activity=self).count()
    
    @property
    def remaining_quota(self):
        return self.total_quota - self.total_apply_count
    
    def update_status(self):
        """自动更新活动状态"""
        from django.utils import timezone
        
        if self.status in ['cancelled', 'ended']:
            return
            
        now = timezone.now()
        batches = self.batches.all()
        
        if not batches.exists():
            return
            
        # 检查是否有进行中的批次
        ongoing_batches = batches.filter(start_time__lte=now, end_time__gte=now)
        if ongoing_batches.exists():
            self.status = 'in_progress'
            self.save()
            return
            
        # 检查是否所有批次都已结束
        all_ended = batches.filter(end_time__lt=now).count() == batches.count()
        if all_ended:
            self.status = 'ended'
            self.save()
            return
            
        # 检查是否已报满
        if self.remaining_quota <= 0:
            self.status = 'full'
            self.save()
            return
            
        # 检查是否有即将开始的批次
        upcoming_batches = batches.filter(start_time__gt=now)
        if upcoming_batches.exists():
            self.status = 'recruiting'
            self.save()
            return

# 报名记录模型
class ActivityApply(models.Model):
    batch = models.ForeignKey(ActivityBatch, on_delete=models.CASCADE, related_name='applies', verbose_name='活动批次', null=True, blank=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applied_activities', verbose_name='报名学生')
    apply_time = models.DateTimeField(auto_now_add=True, verbose_name='报名时间')
    status = models.CharField(max_length=20, choices=(
        ('pending', '待审核'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
        ('cancelled', '已取消'),
    ), default='pending', verbose_name='报名状态')

    class Meta:
        verbose_name = '活动报名'
        verbose_name_plural = '活动报名'
        unique_together = ('batch', 'student')

# 签到记录模型
class CheckinRecord(models.Model):
    apply = models.OneToOneField(ActivityApply, on_delete=models.CASCADE, related_name='checkin', verbose_name='报名记录')
    checkin_time = models.DateTimeField(auto_now_add=True, verbose_name='签到时间')
    checkin_code = models.CharField(max_length=10, unique=True, verbose_name='签到码')
    hours = models.FloatField(validators=[MinValueValidator(0)], default=0, verbose_name='获得时长')
    
    class Meta:
        verbose_name = '签到记录'
        verbose_name_plural = '签到记录'

# 活动收藏模型
class ActivityFavorite(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name='学生')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='favorites', verbose_name='活动')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='收藏时间')
    
    class Meta:
        verbose_name = '活动收藏'
        verbose_name_plural = '活动收藏'
        unique_together = ('student', 'activity')
        ordering = ['-create_time']

# 学生个人不可用时间模型
class StudentUnavailableTime(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unavailable_times', verbose_name='学生')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(verbose_name='结束时间')
    reason = models.CharField(max_length=200, blank=True, verbose_name='原因')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '学生不可用时间'
        verbose_name_plural = '学生不可用时间'
        ordering = ['start_time']

# 活动评价模型
class ActivityRating(models.Model):
    RATING_CHOICES = (
        (1, '非常不满意'),
        (2, '不满意'),
        (3, '一般'),
        (4, '满意'),
        (5, '非常满意'),
    )
    
    DIMENSION_CHOICES = (
        ('organization', '活动组织'),
        ('work_content', '工作内容'),
        ('support', '保障福利'),
        ('management', '老师管理'),
        ('venue', '场地环境'),
    )
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings', verbose_name='学生')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='ratings', verbose_name='活动')
    apply = models.ForeignKey('ActivityApply', on_delete=models.CASCADE, related_name='rating', verbose_name='报名记录')
    
    # 评分信息
    overall_rating = models.IntegerField(choices=RATING_CHOICES, verbose_name='总体评分')
    dimension_ratings = models.JSONField(default=dict, verbose_name='维度评分')
    comment = models.TextField(blank=True, verbose_name='评价内容')
    photos = models.JSONField(default=list, blank=True, verbose_name='现场照片')
    
    # 评价设置
    is_anonymous = models.BooleanField(default=False, verbose_name='匿名评价')
    is_visible = models.BooleanField(default=True, verbose_name='是否可见')
    
    # 回复信息
    teacher_reply = models.TextField(blank=True, verbose_name='老师回复')
    reply_time = models.DateTimeField(null=True, blank=True, verbose_name='回复时间')
    
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='评价时间')
    
    class Meta:
        verbose_name = '活动评价'
        verbose_name_plural = '活动评价'
        unique_together = ('student', 'activity')
        ordering = ['-create_time']

# 志愿者打卡考勤明细模型
class AttendanceRecord(models.Model):
    ATTENDANCE_STATUS_CHOICES = (
        ('normal', '正常'),
        ('late', '迟到'),
        ('early_leave', '早退'),
        ('absent', '缺席'),
        ('no_checkout', '未签退'),
    )
    
    CHECKIN_METHOD_CHOICES = (
        ('qr_code', '扫码签到'),
        ('manual', '老师手动签到'),
        ('batch', '批量签到'),
    )
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records', verbose_name='学生')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='attendance_records', verbose_name='活动')
    batch = models.ForeignKey('ActivityBatch', on_delete=models.CASCADE, related_name='attendance_records', verbose_name='批次')
    apply = models.ForeignKey('ActivityApply', on_delete=models.CASCADE, related_name='attendance', verbose_name='报名记录')
    
    # 打卡信息
    checkin_time = models.DateTimeField(null=True, blank=True, verbose_name='签到时间')
    checkout_time = models.DateTimeField(null=True, blank=True, verbose_name='签退时间')
    actual_hours = models.FloatField(default=0, verbose_name='实际时长(小时)')
    
    # 打卡细节
    checkin_method = models.CharField(max_length=20, choices=CHECKIN_METHOD_CHOICES, verbose_name='签到方式')
    checkin_location = models.CharField(max_length=200, blank=True, verbose_name='签到地点')
    qr_code_id = models.CharField(max_length=50, blank=True, verbose_name='二维码编号')
    
    # 考勤状态
    attendance_status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS_CHOICES, default='normal', verbose_name='考勤状态')
    abnormal_reason = models.TextField(blank=True, verbose_name='异常原因')
    
    # 修改记录
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_attendance', verbose_name='修改人')
    modification_reason = models.TextField(blank=True, verbose_name='修改原因')
    modification_time = models.DateTimeField(null=True, blank=True, verbose_name='修改时间')
    
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '考勤明细'
        verbose_name_plural = '考勤明细'
        ordering = ['-checkin_time']

# 黑名单申诉模型
class BlacklistAppeal(models.Model):
    APPEAL_STATUS_CHOICES = (
        ('pending', '待审核'),
        ('approved', '通过'),
        ('rejected', '驳回'),
    )
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appeals', verbose_name='学生')
    violation = models.ForeignKey('ViolationRecord', on_delete=models.CASCADE, related_name='appeals', verbose_name='违规记录')
    appeal_reason = models.TextField(verbose_name='申诉理由')
    evidence = models.TextField(blank=True, verbose_name='证明材料')
    status = models.CharField(max_length=20, choices=APPEAL_STATUS_CHOICES, default='pending', verbose_name='申诉状态')
    review_opinion = models.TextField(blank=True, verbose_name='审核意见')
    review_time = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_appeals', verbose_name='审核人')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='申诉时间')
    
    class Meta:
        verbose_name = '黑名单申诉'
        verbose_name_plural = '黑名单申诉'
        ordering = ['-create_time']

# 违规记录模型
class ViolationRecord(models.Model):
    VIOLATION_TYPE_CHOICES = (
        ('absent', '无故缺席'),
        ('late', '迟到'),
        ('early_leave', '早退'),
        ('misconduct', '行为不当'),
        ('other', '其他'),
    )
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='violations', verbose_name='学生')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='violations', verbose_name='活动')
    violation_type = models.CharField(max_length=20, choices=VIOLATION_TYPE_CHOICES, verbose_name='违规类型')
    description = models.TextField(verbose_name='违规描述')
    penalty_hours = models.FloatField(default=0, verbose_name='扣除时长')
    ban_days = models.IntegerField(default=0, verbose_name='封禁天数')
    ban_end_time = models.DateTimeField(null=True, blank=True, verbose_name='封禁结束时间')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_violations', verbose_name='记录人')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='记录时间')
    
    class Meta:
        verbose_name = '违规记录'
        verbose_name_plural = '违规记录'
        ordering = ['-create_time']