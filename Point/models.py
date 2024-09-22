from django.db import models

# Create your models here.
class Point(models.Model):
    price = models.CharField(max_length=256)
    point = models.IntegerField()