from django.contrib import admin
from .models import Student, Security, History, Live_Data
from django.contrib.auth.hashers import make_password

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('roll_no', 'name', 'branch')

    def save_model(self, request, obj, form, change):
        if obj.password and not obj.password.startswith('pbkdf2_sha256$'):
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)

@admin.register(Security)
class SecurityAdmin(admin.ModelAdmin):
    list_display = ('security_id',)

    def save_model(self, request, obj, form, change):
        if obj.password and not obj.password.startswith('pbkdf2_sha256$'):
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)

admin.site.register(History)
admin.site.register(Live_Data)