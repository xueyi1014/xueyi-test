from django.apps import AppConfig

class UserConfig(AppConfig):
    # 匹配Django默认主键类型
    default_auto_field = 'django.db.models.BigAutoField'
    # 关键：必须和目录名一致（user）
    name = 'user'