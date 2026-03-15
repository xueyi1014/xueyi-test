from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE = ((1,'student'),(2,'teacher'),(3,'admin'))
    role = models.IntegerField(choices=ROLE, default=1)
    student_id = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=11)
    class Meta:
        db_table = 'user'