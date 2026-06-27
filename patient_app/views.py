from django.shortcuts import render, redirect, get_object_or_404
from personal_account.models import AddPatient
from exercise_app.models import Prescription, PrescriptionExercise
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie

def patient_api_me(request):
    patient_id = request.session.get('patient_id')
    if not patient_id:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        patient = AddPatient.objects.get(id=patient_id)
        latest_prescription = Prescription.objects.filter(patient=patient).order_by('-created_at').first()
        prescription_data = None
        if latest_prescription:
            through_instances = latest_prescription.exercises.all().order_by('order')
            status = getattr(latest_prescription, 'status', 'active')
            notes = getattr(latest_prescription, 'prescription_notes', None) or getattr(latest_prescription, 'notes', None)
            prescription_data = {
                'id': latest_prescription.id,
                'created_at': latest_prescription.created_at.isoformat() if latest_prescription.created_at else '',
                'status': status,
                'prescription_notes': notes,
                'exercises': [
                    {
                        'exercise_name': ti.exercise.exercise_name,
                        'exercise_url': request.build_absolute_uri(ti.exercise.exercise_url) if ti.exercise.exercise_url else None,
                    } for ti in through_instances
                ]
            }
        return JsonResponse({
            'success': True,
            'patient_id': patient.id,
            'patient_name': getattr(patient, 'patient_name', 'Patient'),
            'patient_code': patient.patient_code,
            'diagnosis': getattr(patient, 'patient_diagnosis', None) or 'Not specified',
            'latest_prescription': prescription_data,
        })
    except AddPatient.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)
@ensure_csrf_cookie
def csrf_token_view(request):
    return JsonResponse({'detail': 'CSRF cookie set'})


@csrf_exempt
@require_http_methods(["POST"])
def patient_api_logout(request):
    """Log the patient out by clearing the session.

    Called by the Flutter app's ApiService.logout(). Always returns success so
    the client can safely clear its local cookies regardless of prior state.
    """
    request.session.pop('patient_id', None)
    request.session.flush()
    return JsonResponse({'success': True, 'message': 'Logged out'})

def patient_login(request):
    # If the browser sends a POST request (user clicked the button)
    if request.method == "POST":
        patient_code = request.POST.get('username')
        pin_input = request.POST.get('password')
        
        try:
            patient = AddPatient.objects.get(patient_code=patient_code)
            
            # FOR INTERNAL TESTING ONLY: Plain text comparison
            # ⚠️ REPLACE THIS WITH HASHED PIN IN PRODUCTION
            if patient.patient_contact == pin_input:
                # Store the patient's ID in the session (this logs them in)
                request.session['patient_id'] = patient.id
                
                # ✅ Simply redirect to the dashboard
                # The dashboard will handle fetching the prescription
                return redirect('patient-dashboard')
            else:
                return render(request, 'patient-login.html', {'error': 'Invalid credentials'})
                
        except AddPatient.DoesNotExist:
            return render(request, 'patient-login.html', {'error': 'Invalid credentials'})
    
    # If GET request, show the login form
    return render(request, 'patient-login.html')
    

# ==================== CUSTOM DECORATOR ====================

# Custom decorator to check if patient is logged in
def patient_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('patient_id'):
            return redirect('patient_login')
        return view_func(request, *args, **kwargs)
    return wrapper
# ==================== WEB DASHBOARD ====================

@patient_login_required  # ✅ This checks your custom session
def patient_dashboard(request):
    # Get the logged-in patient
    patient_id = request.session.get('patient_id')
    patient = get_object_or_404(AddPatient, id=patient_id)
    
    # ✅ Fetch the latest prescription HERE (not in login view)
    latest_prescription = Prescription.objects.filter(
        patient=patient
    ).order_by('-created_at').first()
    
    # exercises = []
    # exercises = latest_prescription.exercises.all().order_by('order')
        # ✅ SAFE CHECK: Initialize exercises as empty list if no prescription
    exercises = []
    if latest_prescription:
        exercises = latest_prescription.exercises.all().order_by('order')
    # print (exercises)
    context = {
        'patient': patient,
        'latest_prescription': latest_prescription,
        'exercises': exercises, 
    }
    
    return render(request, 'patient-dashboard-image.html', context)




# ==================== SHARED SERIALIZER ====================

def _build_patient_response(request, patient, message=None):
    """Build the standard patient + latest-prescription JSON payload.

    Mirrors the shape returned by patient_api_login / patient_api_me so all
    login paths (code+PIN, QR) return identical data to the client.
    """
    latest_prescription = Prescription.objects.filter(patient=patient).order_by('-created_at').first()
    prescription_data = None
    if latest_prescription:
        through_instances = latest_prescription.exercises.all().order_by('order')
        status = getattr(latest_prescription, 'status', 'active')
        notes = getattr(latest_prescription, 'prescription_notes', None) or getattr(latest_prescription, 'notes', None)
        prescription_data = {
            'id': latest_prescription.id,
            'created_at': latest_prescription.created_at.isoformat() if latest_prescription.created_at else '',
            'status': status,
            'prescription_notes': notes,
            'exercises': [
                {
                    'exercise_name': ti.exercise.exercise_name,
                    'exercise_url': request.build_absolute_uri(ti.exercise.exercise_url) if ti.exercise.exercise_url else None,
                } for ti in through_instances
            ]
        }

    data = {
        'success': True,
        'patient_id': patient.id,
        'patient_name': getattr(patient, 'patient_name', 'Patient'),
        'patient_code': patient.patient_code,
        'diagnosis': getattr(patient, 'patient_diagnosis', None) or 'Not specified',
        'latest_prescription': prescription_data,
    }
    if message:
        data['message'] = message
    return data


# ==================== MOBILE API: QR LOGIN ====================

@csrf_exempt
@require_http_methods(["POST"])
def patient_api_qr_login(request):
    """Log a patient in from a scanned QR code.

    The patient QR encodes the patient's `qr_token` (a random token). The
    Flutter app scans it and POSTs {"qr_token": "<token>"}. On match we set the
    same session the code+PIN flow uses and return the same payload.
    """
    try:
        data = json.loads(request.body)
        # Accept either key; tolerate a QR that embedded the token in a URL.
        qr_token = (data.get('qr_token') or data.get('token') or '').strip()
        if qr_token and '/' in qr_token:
            qr_token = qr_token.rstrip('/').split('/')[-1]

        if not qr_token:
            return JsonResponse({'success': False, 'error': 'QR token is required'}, status=400)

        try:
            patient = AddPatient.objects.get(qr_token=qr_token)
        except AddPatient.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid or expired QR code'}, status=401)

        request.session['patient_id'] = patient.id
        return JsonResponse(_build_patient_response(request, patient, message='Login successful'))

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        import traceback, logging
        logging.getLogger(__name__).error(traceback.format_exc())
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'}, status=500)


# ==================== MOBILE API LOGIN ====================

@csrf_exempt
@require_http_methods(["POST"])
def patient_api_login(request):
    try:
        data = json.loads(request.body)
        patient_code = data.get('username', '').strip()
        pin_input = data.get('password', '').strip()

        if not patient_code or not pin_input:
            return JsonResponse({'success': False, 'error': 'Username and password are required'}, status=400)

        patient = AddPatient.objects.get(patient_code=patient_code)
        if patient.patient_contact != pin_input:
            return JsonResponse({'success': False, 'error': 'Invalid credentials'}, status=401)

        request.session['patient_id'] = patient.id

        # --- Fetch latest prescription ---
        latest_prescription = Prescription.objects.filter(patient=patient).order_by('-created_at').first()
        prescription_data = None
        if latest_prescription:
            through_instances = latest_prescription.exercises.all().order_by('order')

            status = getattr(latest_prescription, 'status', 'active')
            notes = getattr(latest_prescription, 'prescription_notes', None) or getattr(latest_prescription, 'notes', None)

            prescription_data = {
                'id': latest_prescription.id,
                'created_at': latest_prescription.created_at.isoformat() if latest_prescription.created_at else '',
                'status': status,
                'prescription_notes': notes,
                'exercises': [
                    {
                        'exercise_name': ti.exercise.exercise_name,
                        'exercise_url': request.build_absolute_uri(ti.exercise.exercise_url) if ti.exercise.exercise_url else None,
                    } for ti in through_instances
                ]
            }

        # Build response
        patient_name = getattr(patient, 'patient_name', 'Patient')
        diagnosis = getattr(patient, 'patient_diagnosis', None) or 'Not specified'
        response_data = {
            'success': True,
            'patient_id': patient.id,
            'patient_name': patient_name,
            'patient_code': patient.patient_code,
            'diagnosis': diagnosis,
            'latest_prescription': prescription_data,
            'message': 'Login successful'
        }

        return JsonResponse(response_data)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except AddPatient.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Invalid credentials'}, status=401)
    except Exception as e:
        import traceback
        # Log to server logs (avoid print to stdout)
        import logging
        logger = logging.getLogger(__name__)
        logger.error(traceback.format_exc())
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'}, status=500)