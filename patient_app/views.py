from django.shortcuts import render, redirect, get_object_or_404
from personal_account.models import AddPatient
from exercise_app.models import Prescription, PrescriptionExercise
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

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
    print (exercises)
    context = {
        'patient': patient,
        'latest_prescription': latest_prescription,
        'exercises': exercises, 
    }
    
    return render(request, 'patient-dashboard-image.html', context)




# ==================== MOBILE API LOGIN ====================

import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


@csrf_exempt  # ✅ Disable CSRF for mobile API
@require_http_methods(["POST"])  # ✅ Only allow POST
def patient_api_login(request):
    print("🔵 API Login called!")  # <-- Add this
    try:
        data = json.loads(request.body)
        print(f"📱 Received: {data}")  # <-- Add this
        patient_code = data.get('username')
        pin_input = data.get('password')
        print(f"👤 Searching for: {patient_code} with PIN: {pin_input}")  # <-- Add this
# def patient_api_login(request):
#     try:
#         # Parse the JSON request body from Android
#         data = json.loads(request.body)
#         patient_code = data.get('username')
#         pin_input = data.get('password')
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON format'
        }, status=400)

    # Validate input
    if not patient_code or not pin_input:
        return JsonResponse({
            'success': False,
            'error': 'Username and password are required'
        }, status=400)

    try:
        patient = AddPatient.objects.get(patient_code=patient_code)
    except AddPatient.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Invalid credentials'
        }, status=401)

    # ⚠️ IMPORTANT: Replace this with hashed PIN check in production!
    # For now, plain text comparison (internal testing only)
    if patient.patient_contact == pin_input:
        # ✅ Set session (so web and mobile can share session if needed)
        request.session['patient_id'] = patient.id
        
        # ✅ Return JSON response for Android
        return JsonResponse({
            'success': True,
            'patient_id': patient.id,
            'patient_name': patient.patient_name,
            'patient_code': patient.patient_code,
            'message': 'Login successful'
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Invalid credentials'
        }, status=401)


