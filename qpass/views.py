from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return render(request,"home.html")

def student_login(request):
    if request.method == 'POST':
        pass
    return render(request,"student_login.html")

def security_login(request):
    if request.method == 'POST':
        pass
    return render(request,"security_login.html")

def student(request):
   
    return render(request,"student.html")

def security(request):
    return render(request,"security.html")

def student_history(request):
    return render(request,"student_history.html")

def lateList(request):
    return render(request,"lateList.html")

def logout(request):
    return render(request,"home.html")

# Create your views here.
