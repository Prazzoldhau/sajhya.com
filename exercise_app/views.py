from django.shortcuts import render, get_object_or_404, redirect
from .models import SubRegion, ExerciseMain,Prescription,PrescriptionExercise
from django.http import JsonResponse
from personal_account.models import AddPatient
from datetime import datetime, timedelta,date
from django.utils import timezone   # Django's timezone has .now()
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods




# Create your views here.
def load_exercises(request,patient_id):
    patient = get_object_or_404(AddPatient, id=patient_id)  # single object
    
            # Get all sub-regions for the exercise dropdown
    sub_regions = SubRegion.objects.all()
    
    # Prepare context with both patient and exercise data
    context = {           
        # Exercise information
        'patient': patient,
        'sub_regions': sub_regions,
    }
    
    return render (request, 'exercise-selectable.html', context)


def get_exercises_by_subregion(request):
    sub_region_id = request.GET.get('sub_region_id') 
    if sub_region_id:
        exercises_qs = ExerciseMain.objects.filter(sub_region_fk_id=sub_region_id)
        exercises = exercises_qs.values(
            'id', 'exercise_name', 'exercise_type', 'difficulty_level',
            'default_sets', 'default_reps', 'hold_time_sec', 'exercise_description'
        )
        return JsonResponse({'exercises': list(exercises)})
    return JsonResponse({'exercises': []})


@csrf_exempt
@require_http_methods(["POST"])
def submit_prescription(request):
    try:
        data = json.loads(request.body)
        
        patient_id = data.get('patient_id')
        exercises_data = data.get('exercises', [])
        notes = data.get('notes', '')
        start_date = data.get('start_date')
        duration_days = data.get('duration_days', 30)
        
        # Validate required data
        if not patient_id:
            return JsonResponse({
                'success': False,
                'error': 'Patient ID is required'
            }, status=400)
        
        if not exercises_data:
            return JsonResponse({
                'success': False,
                'error': 'At least one exercise is required'
            }, status=400)
        
        # Get patient from sajhya_app
        try:
            patient = AddPatient.objects.get(id=patient_id)
        except AddPatient.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Patient not found'
            }, status=404)
        
        # Parse dates
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date_obj = timezone.now().date()
        
        end_date_obj = start_date_obj + timedelta(days=duration_days)
        
        # Create prescription
        prescription = Prescription.objects.create(
            patient=patient,
            prescription_notes=notes,
            start_date=start_date_obj,
            end_date=end_date_obj,
            status='active',
            created_by=request.user if request.user.is_authenticated else None
        )
        
        # Add exercises to prescription with ordering
        for index, ex_data in enumerate(exercises_data):
            exercise_id = ex_data.get('id') or ex_data.get('exercise_id')
            
            # Try to get the actual Exercise object from exe_app
            exercise_obj = None
            try:
                exercise_obj = ExerciseMain.objects.get(id=exercise_id)
            except ExerciseMain.DoesNotExist:
                pass  # If exercise doesn't exist in library, still create prescription exercise with snapshot data
            
            PrescriptionExercise.objects.create(
                prescription=prescription,
                exercise=exercise_obj,  # Can be None if exercise was deleted from library
                exercise_id_in_library=exercise_id,
                exercise_name=ex_data.get('exercise_name', 'Unknown Exercise'),
                exercise_type=ex_data.get('exercise_type', 'General'),
                sets=ex_data.get('custom_sets') or ex_data.get('default_sets', 3),
                reps=ex_data.get('custom_reps') or ex_data.get('default_reps', 10),
                difficulty_level=ex_data.get('difficulty_level', 1),
                hold_time_sec=ex_data.get('hold_time_sec', 0),
                exercise_notes=ex_data.get('notes', ''),
                order=index
            )
        
        return JsonResponse({
            'success': True,
            'redirect_url': f'/detail-app/patient-exericse-status/{patient_id}/',  # Add this line
            'prescription_id': prescription.id,
            'message': f'Successfully prescribed {len(exercises_data)} exercises to {patient.patient_name}',
            'prescription': {
                'id': prescription.id,
                'start_date': prescription.start_date.strftime('%Y-%m-%d'),
                'end_date': prescription.end_date.strftime('%Y-%m-%d'),
                'total_exercises': prescription.get_total_exercises()
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def prescription_exercise_details(request):
    return render (request, 'prescription-exercise-details.html')


def patient_prescriptions_view(request, patient_id):
    """View to display all prescriptions for a patient"""
    patient = get_object_or_404(AddPatient, id=patient_id)
    prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at')
    
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
        progress_percentage = (completed_exercises / total_exercises * 100) if total_exercises > 0 else 0
        
        # Check if prescription is active
        today = date.today()
        is_active = (prescription.status == 'active' and 
                    prescription.start_date <= today <= prescription.end_date)
        
        prescriptions_data.append({
            'prescription': prescription,
            'exercises': exercises,
            'total_exercises': total_exercises,
            'completed_exercises': completed_exercises,
            'progress_percentage': round(progress_percentage, 1),
            'is_active': is_active,
            'days_remaining': (prescription.end_date - today).days if is_active else 0
        })
    
    context = {
        'patient': patient,
        'prescriptions': prescriptions_data,
        'total_prescriptions': total_prescriptions,
        'active_prescriptions': active_prescriptions,
        'completed_prescriptions': completed_prescriptions,
        'today': date.today(),
    }
    
    return render(request, 'exercise/patient_prescriptions.html', context)


def session_detail(request):
    return render (request, 'session-details.html')






def add_edit_exercise(request, patient_id):
    patient = get_object_or_404(AddPatient, id=patient_id)

    # 1. Get the most recent prescription for this patient (latest created_at)
    latest_prescription = Prescription.objects.filter(patient=patient).order_by('-created_at').first()

    # 2. Fetch exercises only if a prescription exists
    exercises = []
    if latest_prescription:
        # If you have a ManyToMany field named 'exercises' on Prescription:
        exercises = latest_prescription.exercises.all().order_by('order')
        
        # If Exercise has a ForeignKey to Prescription (named 'prescription'):
        # exercises = Exercise.objects.filter(prescription=latest_prescription).order_by('order')

    return render(request, 'addexercise/add-exercise.html', {'exercises': exercises})