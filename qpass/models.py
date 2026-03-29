from django.db import models

class Student(models.Model):
    roll_no = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=200)
    password = models.CharField(max_length=128)
    branch = models.CharField(max_length=50)
    year = models.CharField(max_length=2)
    phone_no = models.CharField(max_length=15)
    photo = models.ImageField(upload_to='photos/', null=True, blank=True)
    
    def __str__(self):
        return self.roll_no

class Security(models.Model):
    security_id = models.IntegerField(primary_key=True)
    password = models.CharField(max_length=128)

    def __str__(self):
        return f"Security ID: {self.security_id}"

class History(models.Model):
    student_roll_no = models.ForeignKey(Student, on_delete=models.CASCADE)
    Type = models.CharField(max_length=50)
    qr_code = models.CharField(max_length=100, unique=True, null=True)
    out_time = models.DateTimeField(null=True)
    in_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.student_roll_no} - {self.status}"

class Live_Data(models.Model):
    Date = models.DateField(primary_key=True)
    out_Count = models.IntegerField(default=0)
    in_Count = models.IntegerField(default=100)

    def __str__(self):
        return str(self.Date)