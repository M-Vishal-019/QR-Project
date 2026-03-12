from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    
    path('',views.home, name='home'),
    path('student_login/',views.student_login,name='student_login'),
    path('security_login/',views.security_login,name='security_login'),
    path('student_login/student/',views.student,name='student'),
    path('security_login/security/',views.security,name='security'),
    path('student_login/student/student_history/',views.student_history,name='student_history'),
    path('security_login/security/lateList/',views.lateList,name='security'),
    path('student_login/student/logout/',views.logout,name='logout'),

]
