from django.db import models

class Student(models.Model):
    roll_no = models.CharField(primary_key=True),
    password = models.CharField(max_length=20),
    branch = models.CharField(),
    year = models.CharField(max_length=2),
    phone_no = models.CharField(max_length=15),
    photo = models.ImageField();

    #@property
    #def total_outings(self):
    #   return self.outingrecord_set.count() 

    def __str__(self):
        return self.roll_no

class Security(models.Model):
    security_id = models.IntegerField(primary_key=True),
    student_password = models.CharField(max_length=20),

class OutingRecord(models.Model):
    student_roll_no = models.ForeignKey(Student, on_delete=models.CASCADE),
    Type = models.CharField(max_length=50),
    qr_code = models.CharField(max_length=100, unique=True),
    out_time = models.DateTimeField(),
    in_time = models.DateTimeField(null=True, blank=True),
    status = models.CharField(max_length=20),
    is_late = models.BooleanField(default=False),
    created_at = models.DateTimeField(auto_now_add=True),
    student_TOC = models.IntegerField(),
    student_TIC = models.IntegerField()
    
    def _str_(self):
        return f"{self.student_roll_no.roll_no} - {self.out_time}"
