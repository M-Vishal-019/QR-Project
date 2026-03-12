
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Student, Staff, OutingRecord
from datetime import datetime
import uuid


def home(request):
    return render(request,"home.html")

def student_login(request):
    if request.method == 'POST':
        roll_no = request.POST.get('roll_no')
        password = request.POST.get('password')
        student = Student.objects.filter(roll_no=roll_no, password=password).first()
        if student:
            request.session['student_roll_no'] = student.roll_no
            return redirect('student_dashboard')
        else:
            return render(request, 'student_login.html', {'error': 'Invalid credentials'})  
    return render(request, 'student_login.html')


def staff_login(request):
    if request.method == 'POST':
        staff_id = request.POST.get('staff_id')
        password = request.POST.get('password')
        
        staff = Staff.objects.filter(staff_id=staff_id, password=password).first()
        
        if staff:
            request.session['staff_id'] = staff.staff_id
            return redirect('security_dashboard')
        else:
            return render(request, 'security_login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'security_login.html')

def student_dashboard(request):
    roll_no = request.session.get('student_roll_no')
    
    if not roll_no:
        return redirect('student_login')
    
    student = Student.objects.get(roll_no=roll_no)
    outings = OutingRecord.objects.filter(student_roll_no=student).order_by('-out_time')
    
    active_outing = OutingRecord.objects.filter(
        student_roll_no=student,
        in_time__isnull=True
    ).first()
    
    if request.method == 'POST':
        action = request.POST.get('action') 
        outing_type = request.POST.get('outing_type')
        
        if action == 'out':
            qr_code = str(uuid.uuid4())[:8].upper() 
            OutingRecord.objects.create(
                student_roll_no=student,
                outing_type=outing_type,
                qr_code=qr_code,
                out_time=datetime.now(),
                status='Out'
            )
            student.total_out_count += 1
            student.save()
            
            return redirect('student_dashboard')
        
        elif action == 'in' and active_outing:
            active_outing.in_time = datetime.now()
            active_outing.status = 'Completed'
            if active_outing.out_time.hour >= 18:
                active_outing.is_late = True
            active_outing.save()
            
            student.total_in_count += 1
            student.save()
            
            return redirect('student_dashboard')
    
    context = {
        'student': student,
        'outings': outings,
        'active_outing': active_outing,
        'date': datetime.now().strftime('%d/%m/%Y'),
        'time': datetime.now().strftime('%I:%M %p')
    }
    return render(request, 'student.html', context)


def security_dashboard(request):
    staff_id = request.session.get('staff_id')
    
    if not staff_id:
        return redirect('staff_login')
    
    context = {
        'date': datetime.now().strftime('%d/%m/%Y')
    }
    return render(request, 'security.html', context)


def student_history(request):
    roll_no = request.session.get('student_roll_no')
    
    if not roll_no:
        return redirect('student_login')
    
    student = Student.objects.get(roll_no=roll_no)
    outings = OutingRecord.objects.filter(student_roll_no=student).order_by('-out_time')
    
    context = {
        'student': student,
        'outings': outings
    }
    return render(request, 'student_history.html', context)


def late_list(request):
    staff_id = request.session.get('staff_id')
    
    if not staff_id:
        return redirect('staff_login')
    late_records = OutingRecord.objects.filter(is_late=True).order_by('-out_time')
    
    context = {
        'late_records': late_records,
        'date': datetime.now().strftime('%d/%m/%Y')
    }
    return render(request, 'lateList.html', context)

def logout(request):
    return render(request,"home.html")

# Create your views here.
