from django.contrib import admin
from .models import Student, Security, History, Live_Data

admin.site.register(Student)
admin.site.register(Security)
admin.site.register(History)
admin.site.register(Live_Data)