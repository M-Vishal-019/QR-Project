from django.db import models

# Create your models here.
class Student(models.Model):
    student_roll_no = models.CharField(primary_key=True),
    student_password = models.CharField(max_length=20),
    student_branch = models.CharField(),
    student_year = models.CharField(max_length=2),
    student_phone_no = models.CharField(max_length=15),
    student_TOC = models.IntegerField(),
    student_TIC = models.IntegerField()

    def __str__(self):
        return self.roll_no
    

class Security(models.Model):
    security_id = models.IntegerField(primary_key=True),



