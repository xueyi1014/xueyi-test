from django.apps import AppConfig

class ActivityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # 关键：必须和目录名一致（activity）
    name = 'activity'