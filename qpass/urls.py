from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    
    path('admin/',admin.site.urls),
    path('',views.home, name='home'),
    path('student_login/',views.student_login,name='student_login'),
    path('security_login/',views.security_login,name='security_login'),
    path('student_login/student/',views.student_dashboard,name='student'),
    path('security_login/security/',views.security_dashboard,name='security'),
    path('student_login/student/student_history/',views.student_history,name='student_history'),
    path('security_login/security/lateList/',views.late_list,name='latelist'),
    path('student_login/student/logout/',views.logout,name='logout'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)