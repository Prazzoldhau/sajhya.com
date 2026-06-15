from django.shortcuts import render, get_object_or_404
from datetime import date
from personal_account.models import AddPatient, Clinic
from exercise_app.models import Prescription,PrescriptionExercise
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone


# Create your views here.
def patient_detail(request):
    return render (request, 'patient-detail-dashboard.html')


def patient_exercise_status(request, patient_id):
   
    """View to display all prescriptions for a patient"""
    patient = get_object_or_404(AddPatient, id=patient_id)
    # clinic_id = patient.origin_clinic.id   # Get clinic ID from patient
    # clinic_id = patient.origin_clinic.id if patient.origin_clinic else '',
    clinic_id = patient.origin_clinic.id if patient.origin_clinic else None
    prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')
    
    user = request.user
    userType = user.user_type


    
    # Calculate statistics
    total_prescriptions = prescriptions.count()
    active_prescriptions = prescriptions.filter(status='active').count()
    completed_prescriptions = prescriptions.filter(status='completed').count()
    
    # Prepare prescriptions data with exercises
    prescriptions_data = []
    for prescription in prescriptions:
        exercises = prescription.exercises.all().order_by('order')
        
        # Calculate progress
        total_exercises = exercises.count()
        completed_exercises = exercises.filter(is_completed=True).count()

        
        # Check if prescription is active
        today = date.today()
        is_active = (prescription.status == 'active' and 
                    prescription.start_date <= today <= prescription.end_date)
        
        prescriptions_data.append({
            'prescription': prescription,
            'exercises': exercises,
            'total_exercises': total_exercises,
            'completed_exercises': completed_exercises,
            'is_active': is_active,
            'days_remaining': (prescription.end_date - today).days if is_active else 0
        })
    
    context = {
        'patient': patient,
        'prescriptions': prescriptions_data,
        'total_prescriptions': total_prescriptions,
        'active_prescriptions': active_prescriptions,
        'completed_prescriptions': completed_prescriptions,
        'clinic_id': clinic_id,
        'today': date.today(),
        "user_type": userType,
    }
    
    
    return render (request, 'patient-exercise-state.html', context)




def latest_prescription(request, patient_id):
    patient = get_object_or_404(AddPatient, id=patient_id)
    latest_prescription = Prescription.objects.filter(patient=patient).order_by('-created_at').first()
    if not latest_prescription:
        return JsonResponse({'error': 'No prescription found'}, status=404)
    
    exercises_list = []
    for ex in latest_prescription.exercises.all().order_by('order'):
        exercises_list.append({
            'id': ex.id,
            'exercise_name': ex.exercise_name,
            'difficulty_level': ex.difficulty_level,
            'sets': getattr(ex, 'sets', None),   # adjust to your through model
            'reps': getattr(ex, 'reps', None),
            'is_completed': getattr(ex, 'is_completed', False),
        })
    
    return JsonResponse({
        'prescription_id': latest_prescription.id,
        'status': latest_prescription.status,
        'start_date': latest_prescription.start_date.isoformat(),
        'end_date': latest_prescription.end_date.isoformat(),
        'exercises': exercises_list,
    })


@csrf_exempt
@require_http_methods(["POST"])
def toggle_exercise_completion(request, exercise_id):
    try:
        exercise = PrescriptionExercise.objects.get(id=exercise_id)
        data = json.loads(request.body)
        is_completed = data.get('is_completed', False)

        exercise.is_completed = is_completed
        exercise.completed_at = timezone.now() if is_completed else None
        exercise.save()

        # Get the parent prescription
        prescription = exercise.prescription
        exercises = prescription.exercises.all()
        total_exercises = exercises.count()
        completed_exercises = exercises.filter(is_completed=True).count()
        progress_percentage = (completed_exercises / total_exercises * 100) if total_exercises > 0 else 0

        # Check if the prescription just became fully completed
        just_completed = (completed_exercises == total_exercises) and total_exercises > 0

        return JsonResponse({
            'success': True,
            'prescription_id': prescription.id,
            'completed_exercises': completed_exercises,
            'total_exercises': total_exercises,
            'progress_percentage': round(progress_percentage, 1),
            'prescription_completed': just_completed,
            'exercise_id': exercise_id,
            'is_completed': is_completed
        })

    except PrescriptionExercise.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Exercise not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)