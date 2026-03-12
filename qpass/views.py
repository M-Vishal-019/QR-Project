from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Student, Security, OutingRecord  
import uuid
import qrcode
from io import BytesIO
import json
import base64

def home(request):
    return render(request, "home.html")

def student_login(request):
    if request.method == 'POST':
        roll_no = request.POST.get('roll_no')
        password = request.POST.get('password')
        student = Student.objects.filter(roll_no=roll_no, password=password).first()
        if student:
            request.session['roll_no'] = student.roll_no
            return redirect('student_dashboard')
        else:
            return render(request, 'student_login.html', {'error': 'Invalid credentials'})  
    return render(request, 'student_login.html')

def student_dashboard(request):
    roll_no = request.session.get('roll_no')
    if not roll_no:
        return redirect('student_login')
    
    student = Student.objects.get(roll_no=roll_no)
    
    active_outing = OutingRecord.objects.filter(
        roll_no=student, 
        status__in=['Pending_Out', 'Out', 'Pending_In']
    ).first()

    qr_image = None
    message = None

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'generate_qr':
            if not active_outing:
                outing_type = request.POST.get('outing_type')
                qr_string = str(uuid.uuid4()).upper()[:10]
                
                OutingRecord.objects.create(
                    roll_no=student,
                    outing_type=outing_type,
                    qr_code=qr_string,
                    status='Pending_Out' 
                )
                message = "Show this QR to Security for EXIT."

            elif active_outing.status == 'Out':
                qr_string = str(uuid.uuid4()).upper()[:10]
                active_outing.qr_code = qr_string
                active_outing.status = 'Pending_In' 
                active_outing.save()
                message = "Show this QR to Security for ENTRY."
        
            active_outing = OutingRecord.objects.filter(
                roll_no=student, 
                status__in=['Pending_Out', 'Out', 'Pending_In']
            ).first()

    if active_outing and active_outing.status in ['Pending_Out', 'Pending_In']:
        img = qrcode.make(active_outing.qr_code)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    context = {
        'student': student,
        'active_outing': active_outing,
        'qr_image': qr_image,
        'message': message,
        'date': timezone.now().strftime('%d/%m/%Y'),
        'time': timezone.now().strftime('%I:%M %p')
    }
    return render(request, 'student.html', context)

def student_history(request):
    roll_no = request.session.get('roll_no')
    if not roll_no: return redirect('student_login')
    
    student = Student.objects.get(roll_no=roll_no)
    outings = OutingRecord.objects.filter(roll_no=student).order_by('-out_time')
    
    context = {'student': student, 'outings': outings}
    return render(request, 'student_history.html', context)


def security_login(request):
    if request.method == 'POST':
        staff_id = request.POST.get('security_id')
        password = request.POST.get('password')
        staff = Security.objects.filter(staff_id=staff_id, password=password).first()
        if staff:
            request.session['security_id'] = staff.staff_id
            return redirect('security_dashboard')
        else:
            return render(request, 'security_login.html', {'error': 'Invalid credentials'})
    return render(request, 'security_login.html')

@csrf_exempt
def security_dashboard(request):
    staff_id = request.session.get('security_id')
    if not staff_id:
        return redirect('security_login')
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            qr_code_input = data.get('qr_code')
            
            record = OutingRecord.objects.filter(qr_code=qr_code_input).first()
            
            if not record:
                return JsonResponse({'success': False, 'message': 'Invalid QR Code'})
            student = record.roll_no
            response_data = {
                'success': True,
                'name': student.name,
                'roll': student.roll_no,
                'outing_type': record.outing_type,
                'total_outings': OutingRecord.objects.filter(roll_no=student, status='Completed').count()
            }
            if record.status == 'Pending_Out':
                record.status = 'Out'
                record.out_time = timezone.now()
                record.save()
                response_data['action'] = 'EXIT'
                response_data['message'] = 'Exit Granted'

            elif record.status == 'Pending_In':
                record.in_time = timezone.now()
                record.status = 'Completed'
                
                if record.in_time.hour >= 21:
                    record.is_late = True
                
                record.save()
                response_data['action'] = 'ENTRY'
                response_data['message'] = 'Entry Granted'
                response_data['is_late'] = record.is_late
                
                response_data['total_outings'] = OutingRecord.objects.filter(roll_no=student, status='Completed').count()
            
            else:
                return JsonResponse({'success': False, 'message': f'QR Code already used or invalid status: {record.status}'})

            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    context = {
        'date': timezone.now().strftime('%d/%m/%Y')
    }
    return render(request, 'security.html', context)

def late_list(request):
    staff_id = request.session.get('security_id')
    if not staff_id:
        return redirect('security_login')
    
    current_time = timezone.now()
    returned_late = OutingRecord.objects.filter(is_late=True)
    active_late = OutingRecord.objects.none()
    if current_time.hour >= 21:
        active_late = OutingRecord.objects.filter(status__in=['Out', 'Pending_In'])
        
    late_records = (returned_late | active_late).distinct().order_by('-out_time')
    
    context = {'late_records': late_records, 'date': current_time.strftime('%d/%m/%Y')}
    return render(request, 'lateList.html', context)

def logout(request):
    request.session.flush()
    return redirect('home')