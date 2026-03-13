from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Student, Security, OutingRecord
import uuid
import qrcode
from io import BytesIO
import base64
from django.db import transaction, IntegrityError
from django.conf import settings
from django.contrib.auth.hashers import check_password
import json
import logging


logger = logging.getLogger(__name__)

STATUS_PENDING_OUT = 'Pending_Out'
STATUS_PENDING_IN  = 'Pending_In'
STATUS_OUT         = 'Out'
STATUS_COMPLETED   = 'Completed'

LATE_HOUR = getattr(settings, 'LATE_HOUR_THRESHOLD', 21)


def home(request):
    return render(request, "home.html")


def student_login(request):
    if request.method == 'POST':
        roll_no  = request.POST.get('roll_no', '').strip()
        password = request.POST.get('password', '')

        student = Student.objects.filter(roll_no=roll_no).first()

        if student and check_password(password, student.password):
            request.session['roll_no'] = student.roll_no
            return redirect('student_dashboard')

        return render(request, 'student_login.html', {'error': 'Invalid credentials'})

    return render(request, 'student_login.html')


def student_dashboard(request):
    roll_no = request.session.get('roll_no')
    if not roll_no:
        return redirect('student_login')

    student = get_object_or_404(Student, roll_no=roll_no)

    active_outing = OutingRecord.objects.filter(
        roll_no=student,
        status__in=[STATUS_PENDING_OUT, STATUS_OUT, STATUS_PENDING_IN]
    ).first()

    qr_image = None
    message  = None

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
                    status=STATUS_PENDING_OUT
                )
                message = "Show this QR to Security for EXIT."

            elif active_outing.status == STATUS_OUT:
                qr_string = str(uuid.uuid4()).upper()[:10]
                active_outing.qr_code = qr_string
                active_outing.status = STATUS_PENDING_IN
                active_outing.save()
                message = "Show this QR to Security for ENTRY."

            active_outing = OutingRecord.objects.filter(
                roll_no=student,
                status__in=[STATUS_PENDING_OUT, STATUS_OUT, STATUS_PENDING_IN]
            ).first()

    if active_outing and active_outing.status in [STATUS_PENDING_OUT, STATUS_PENDING_IN]:
        img    = qrcode.make(active_outing.qr_code)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    context = {
        'student'      : student,
        'active_outing': active_outing,
        'qr_image'     : qr_image,
        'message'      : message,
        'date'         : timezone.now().strftime('%d/%m/%Y'),
        'time'         : timezone.now().strftime('%I:%M %p'),
    }
    return render(request, 'student.html', context)


def student_history(request):
    roll_no = request.session.get('roll_no')
    if not roll_no:
        return redirect('student_login')

    student = get_object_or_404(Student, roll_no=roll_no)

    outings = OutingRecord.objects.filter(roll_no=student).order_by('-id')

    context = {'student': student, 'outings': outings}
    return render(request, 'student_history.html', context)



def security_login(request):
    if request.method == 'POST':
        security_id = request.POST.get('security_id', '').strip()
        password    = request.POST.get('password', '')

        security = Security.objects.filter(security_id=security_id).first()

        if security and check_password(password, security.password):
            request.session['security_id'] = security.security_id
            return redirect('security_dashboard')

        return render(request, 'security_login.html', {'error': 'Invalid credentials'})

    return render(request, 'security_login.html')


@csrf_exempt  
def security_dashboard(request):
    staff_id = request.session.get('security_id')
    if not staff_id:
        return redirect('security_login')

    if request.method == 'POST':
        try:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse(
                    {'success': False, 'message': 'Invalid JSON format'}, status=400
                )

            qr_code_input = data.get('qr_code', '').strip()
            if not qr_code_input:
                return JsonResponse(
                    {'success': False, 'message': 'QR Code missing'}, status=400
                )

            with transaction.atomic():
                record = (
                    OutingRecord.objects
                    .select_related('roll_no')
                    .select_for_update()       
                    .filter(qr_code=qr_code_input)
                    .first()
                )

                if not record:
                    return JsonResponse(
                        {'success': False, 'message': 'Invalid QR Code'}, status=404
                    )

                student = record.roll_no
                now     = timezone.now()      

                total_outings = OutingRecord.objects.filter(
                    roll_no=student, status=STATUS_COMPLETED
                ).count()

                response_data = {
                    'success'      : True,
                    'name'         : student.name,
                    'roll'         : student.roll_no,
                    'outing_type'  : record.outing_type,
                    'total_outings': total_outings,
                }

                if record.status == STATUS_PENDING_OUT:
                    record.status   = STATUS_OUT
                    record.out_time = now
                    record.save()

                    response_data['action']  = 'EXIT'
                    response_data['message'] = 'Exit Granted'

                elif record.status == STATUS_PENDING_IN:
                    record.in_time = now
                    record.status  = STATUS_COMPLETED
                    record.is_late = now.hour >= LATE_HOUR   
                    record.save()

                  
                    total_outings = OutingRecord.objects.filter(
                        roll_no=student, status=STATUS_COMPLETED
                    ).count()

                    response_data['action']        = 'ENTRY'
                    response_data['message']       = 'Entry Granted'
                    response_data['is_late']       = record.is_late
                    response_data['total_outings'] = total_outings

               
                else:
                    return JsonResponse(
                        {'success': False, 'message': f'Invalid Status: {record.status}'},
                        status=400
                    )

                return JsonResponse(response_data)

        except IntegrityError as e:
            logger.error(f"Database Integrity Error in security_dashboard: {e}")
            return JsonResponse(
                {'success': False, 'message': 'Database error occurred'}, status=500
            )
        except Exception as e:
            logger.error(f"Unexpected Error in security_dashboard: {e}")
            return JsonResponse(
                {'success': False, 'message': 'Internal server error'}, status=500
            )

    context = {'date': timezone.now().strftime('%d/%m/%Y')}
    return render(request, 'security.html', context)


def late_list(request):
    security_id = request.session.get('security_id')
    if not security_id:
        return redirect('security_login')

    from django.db.models import Q

    current_time = timezone.now()

    late_filter = Q(is_late=True)
    if current_time.hour >= LATE_HOUR:
        late_filter |= Q(status__in=[STATUS_OUT, STATUS_PENDING_IN])

    late_records = (
        OutingRecord.objects
        .filter(late_filter)
        .distinct()
        .order_by('-id')     
    )

    context = {
        'late_records': late_records,
        'date'        : current_time.strftime('%d/%m/%Y'),
    }
    return render(request, 'lateList.html', context)

@require_POST
def logout(request):
    request.session.flush()
    return redirect('home')