from django.shortcuts import render, redirect, get_object_or_404
from personal_account.models import AddPatient
from django.shortcuts import get_object_or_404
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
    


# Custom decorator to check if patient is logged in
def patient_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('patient_id'):
            return redirect('patient_login')
        return view_func(request, *args, **kwargs)
    return wrapper

@patient_login_required  # ✅ This checks your custom session
def patient_dashboard(request):
    # Get the logged-in patient
    patient_id = request.session.get('patient_id')
    patient = get_object_or_404(AddPatient, id=patient_id)
    
    # ✅ Fetch the latest prescription HERE (not in login view)
    latest_prescription = Prescription.objects.filter(
        patient=patient
    ).order_by('-created_at').first()
    
    
    exercises = latest_prescription.exercises.all().order_by('order')
    print (exercises)
    context = {
        'patient': patient,
        'latest_prescription': latest_prescription,
        'exercises': exercises, 
    }
    
    return render(request, 'patient-dashboard.html', context)