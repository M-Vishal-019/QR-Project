from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Student, Security,History, Live_Data
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import uuid
from datetime import datetime, time
from django.contrib.auth.hashers import check_password


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
            if check_password(password, student.password):
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
    error = None
    last_record = History.objects.filter(student_roll_no=student).order_by('-out_time').first()
    
    is_out = last_record and last_record.status == 'Out'

    if request.method == 'POST':
        if last_record and last_record.status == 'Pending':
            qr_text = f"Roll:{student.roll_no}|ID:{last_record.qr_code}"
        
        else:
            direction = "IN" if is_out else "OUT"
            
            outing_type = last_record.Type if is_out else request.POST.get('OUT')
            
            unique_id = str(uuid.uuid4())[:8].upper()

            History.objects.create(
                student_roll_no=student,
                Type=outing_type,
                qr_code=unique_id,
                out_time=timezone.now(),
                status='Pending'
            )
            qr_text = f"Roll:{student.roll_no}|Dir:{direction}|ID:{unique_id}"

    context = {
        'student': student,  
        'qr_text': qr_text, 
        'error': error,
        'is_out': is_out  
    }
    return render(request, 'student.html', context)


def student_history(request):
    roll_no = request.session.get('roll_no')
    if not roll_no:
        return redirect('student_login')
    
    student = get_object_or_404(Student, roll_no=roll_no)
    
    now = timezone.localtime(timezone.now())
    selected_date_str = request.GET.get('date')
    
    if selected_date_str:
        try:
            target_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = now.date()
    else:
        target_date = now.date()

    history_records = History.objects.filter(
        student_roll_no=roll_no,
        out_time__date=target_date
    ).order_by('-out_time')

    context = {
        'student': student,
        'history': history_records,
        'display_date': target_date.strftime('%d/%m/%Y'),
        'input_date': target_date.strftime('%Y-%m-%d'),
        'student_roll_no': roll_no
    }
    return render(request, 'student_history.html', context)


def security_login(request):
    if request.method == 'POST':
        staff_id = request.POST.get('staff_id')
        password = request.POST.get('password')

        try:
            security = Security.objects.get(security_id=staff_id)
            if check_password(password, security.password):
                request.session['security_id'] = security.security_id
                return redirect('security')
            else :
                return render(request, 'security_login.html', {'error': 'Invalid Password'})
        except (Security.DoesNotExist, ValueError):
            return render(request, 'security_login.html', {'error': 'Invalid Staff Credentials'})
            
    return render(request, 'security_login.html')


def security_dashboard(request):
    security_id = request.session.get('security_id')
    if not security_id:
        return redirect('security_login')

    def get_live_counts():
        total_students = Student.objects.count() #
        in_campus = 0
        outing_students = 0
        home_students = 0

        for student in Student.objects.all():
            last_record = History.objects.filter(student_roll_no=student).exclude(status='Pending').order_by('-out_time').first() 
            if not last_record or last_record.status == 'In':
                in_campus += 1
            elif last_record.status == 'Out':
                if last_record.Type == 'Outing':
                    outing_students += 1
                elif last_record.Type == 'Home':
                    home_students += 1
        
        return {
            'total': total_students,
            'in_campus': max(0,in_campus),
            'out_outing': outing_students,
            'out_home': home_students
        }

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            raw_qr_data = data.get('qr_data','') 
            
            roll_no = None
            qr_id = None
            
            if "Roll:" in raw_qr_data:
                parts = raw_qr_data.split('|')
                for part in parts:
                    if part.startswith('Roll:'): roll_no = part.split(':')[1]
                    if part.startswith('ID:'): qr_id = part.split(':')[1]
            else:
                roll_no = raw_qr_data

            student = Student.objects.filter(roll_no=roll_no).first()
            if not student:
                return JsonResponse({'status': 'error', 'message': 'Student not found.'})

            if action == 'verify':
                if not qr_id:
                    return JsonResponse({'status': 'error', 'message': 'Invalid QR Format.'})
                
                record = History.objects.filter(qr_code=qr_id, student_roll_no=student).first()
                if not record:
                    return JsonResponse({'status': 'error', 'message': 'QR Code not recognized.'})
                if record.status != 'Pending':
                    return JsonResponse({'status': 'error', 'message': f'Already used for {record.status}.'})

                last_event = History.objects.filter(student_roll_no=student).exclude(status='Pending').order_by('-out_time').first()
                direction = "Inward (Returning)" if (last_event and last_event.status == 'Out') else "Outward (Leaving)"

                return JsonResponse({
                    'status': 'success',
                    'student': {
                        'name': student.name,
                        'roll_no': student.roll_no,
                        'branch': student.branch,
                        'year': student.year,
                        'direction': direction,
                        'photo_url': student.photo.url if student.photo else '/static/student_logo.webp'
                    }
                })

            elif action == 'confirm':
                decision = data.get('decision')
                if decision == 'Accept':
                    record = History.objects.filter(qr_code=qr_id, status='Pending').first()
                    if record:
                        last_event = History.objects.filter(student_roll_no=student).exclude(id=record.id).order_by('-out_time').first()
                        record.status = 'In' if (last_event and last_event.status == 'Out') else 'Out'
                        record.out_time = timezone.now()
                        record.save() 
                        
                        return JsonResponse({
                            'status': 'success', 
                            'message': f'Marked {record.status} successfully.',
                            'counts': get_live_counts() 
                        })
                return JsonResponse({'status': 'error', 'message': 'Action rejected or record missing.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'System Error: {str(e)}'})

    return render(request, 'security.html', get_live_counts())


def late_list(request):
    security_id = request.session.get('security_id')
    if not security_id:
        return redirect('security_login')

    now = timezone.localtime(timezone.now())
    today_date = now.date()
    
    selected_date_str = request.GET.get('date')
    
    if selected_date_str:
        try:
            target_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            target_date = today_date
    else:
        target_date = today_date
    
    late_records = []
    
    curfew_time = time(15, 55) 

    late_records = History.objects.filter(
        out_time__date=target_date,
        status='Out'
    ).exclude(Type='Home').select_related('student_roll_no').order_by('out_time')
    if target_date == today_date and now.time() < curfew_time:
        late_records = []

    context = {
        'late_records': late_records,
        'input_date': target_date.strftime('%Y-%m-%d'),
    }
    return render(request, 'lateList.html', context)


def logout(request):
    request.session.flush()
    return redirect('home')