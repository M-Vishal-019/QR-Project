
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from .models import Student, Security,History, Live_Data
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt




def home(request):
    return render(request, "home.html")

def student_login(request):
    if request.method == 'POST':
        roll_no = request.POST.get('student_roll_no', '').strip()
        password = request.POST.get('password', '')
        
        if not roll_no or not password:
            return render(request, 'student_login.html', {'error': 'Please enter both Roll Number and Password'})

        try:
            student = Student.objects.get(roll_no=roll_no)
            if student.password == password:
                request.session['roll_no'] = student.roll_no
                return redirect('student')
            else:
                return render(request, 'student_login.html', {'error': 'Invalid Password'})  
        except Student.DoesNotExist:
            return render(request, 'student_login.html', {'error': 'Roll Number not found'})
        
    return render(request, 'student_login.html')

def student_dashboard(request):
    roll_no = request.session.get('roll_no')
    if not roll_no:
        return redirect('student_login')
    
    student = get_object_or_404(Student, roll_no=roll_no)
    qr_text = None

    if request.method == 'POST':
        outing_type = request.POST.get('OUT')
        unique_id = str(uuid.uuid4())[:8].upper()

        History.objects.create(
            student_roll_no=student,
            Type=outing_type,
            qr_code=unique_id,
            out_time=timezone.now(),
            status='Pending'
        )

        qr_text = f"Roll:{student.roll_no}\nType:{outing_type}\nID:{unique_id}"

    return render(request, 'student.html', {'student': student, 'qr_text': qr_text})

def student_history(request):
    roll_no = request.session.get('roll_no')
    if not roll_no:
        return redirect('student_login')
    
    # Matches ForeignKey name 'student_roll_no' in your models.py
    user_history = History.objects.filter(student_roll_no=roll_no).order_by('-out_time')
    return render(request, 'student_history.html', {'history': user_history})


def security_login(request):
    if request.method == 'POST':
        staff_id = request.POST.get('staff_id')
        password = request.POST.get('password')

        try:
            security = Security.objects.get(security_id=staff_id)
            if security.student_password == password:
                request.session['security_id'] = security.security_id
                return redirect('security')
        except (Security.DoesNotExist, ValueError):
            return render(request, 'security_login.html', {'error': 'Invalid Staff Credentials'})
            
    return render(request, 'security_login.html')



@csrf_exempt
def security_dashboard(request):
    security_id = request.session.get('security_id')
    if not security_id:
        return redirect('security_login')

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            qr_id = data.get('qr_id')
            
            # 1. Find the History record
            record = History.objects.get(qr_code=qr_id)
            student = record.student_roll_no # Get the Student object
            
            stats, created = Live_Data.objects.get_or_create(Date=timezone.now().date())
            
            if record.status == 'Pending':
                record.status = 'Out'
                stats.out_Count += 1
                msg = "Verified: Student Leaving"
            elif record.status == 'Out':
                record.status = 'In'
                record.in_time = timezone.now()
                stats.in_Count += 1
                msg = "Verified: Student Returned"
            else:
                return JsonResponse({'success': False, 'message': 'QR Already Used'})

            record.save()
            stats.save()

            return JsonResponse({
                'success': True,
                'message': msg,
                'student_details': {
                    'roll_no': student.roll_no,
                    'branch': student.branch,
                    'phone': student.phone_no,
                    'photo_url': student.photo.url if student.photo else '/static/default_user.png',
                    'year': student.year,
                    'status': record.status
                }
            })

        except History.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid QR Code'})

    return render(request, 'security.html')

def late_list(request):
    security_id = request.session.get('security_id')
    if not security_id:
        return redirect('security_login')

    late_records = History.objects.filter(in_time__isnull=True)

    context = {
        'late_records': late_records,
        'date': timezone.now().strftime('%d/%m/%Y'),
    }
    return render(request, 'lateList.html', context)

def logout(request):
    request.session.flush()
    return redirect('home')