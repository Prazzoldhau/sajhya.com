from django.shortcuts import render
from personal_account.models import AddPatient
from .models import TreatmentSession
from datetime import datetime
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from .models import TreatmentSession, Modality, TreatmentSessionModality
import json
from django.urls import reverse


# Create your views here.
def start_prescription(request, patient_id):
    patient = get_object_or_404(AddPatient, id=patient_id)
    # patient = AddPatient.objects.filter(id=patient_id)
    existing_count = TreatmentSession.objects.filter(patient_id=patient_id).count()
    past_session = patient.completed_session
    new_session_number = past_session + existing_count + 1   # first session → 1
    
    context = {
        "patient": patient,
        "new_session": new_session_number,
    
    }
    
    
    return render (request, 'prescription-page.html', context)






@require_http_methods(["POST"])
@csrf_exempt  # only if needed for your API client
def save_treatment_session(request):
    try:
        # Parse request body
        data = json.loads(request.body)
        
        # -------- Validation (no database changes yet) --------
        
        # Required fields
        required_fields = ['patient_id', 'session_number']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'success': False, 'error': f'Missing required field: {field}'})
        
        # Validate session_number is numeric if needed (optional)
        if not isinstance(data['session_number'], int) and not data['session_number'].isdigit():
            return JsonResponse({'success': False, 'error': 'session_number must be an integer'})
        
        # Validate modalities is a list
        modalities_data = data.get('modalities', [])
        if not isinstance(modalities_data, list):
            return JsonResponse({'success': False, 'error': 'modalities must be a list'})
        
        # Validate each modality has a 'name'
        for idx, mod in enumerate(modalities_data):
            if 'name' not in mod:
                return JsonResponse({'success': False, 'error': f'Modality at index {idx} missing "name"'})
        
        # Validate next_session date format (if provided)
        next_session = data.get('next_session')
        if next_session:
            try:
                datetime.strptime(next_session, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'success': False, 'error': 'next_session must be in YYYY-MM-DD format'})
        
        # -------- Atomic creation --------
        with transaction.atomic():
            # Get patient (raises 404 if not found – will rollback)
            patient = get_object_or_404(AddPatient, id=data['patient_id'])
            # clinic_id = patient.origin_clinic.id
            clinic_id = patient.origin_clinic.id if patient.origin_clinic else None
            
            redirectTarget = data.get('redirect_to', 'exercise')  # default to exercise
            if redirectTarget == 'exercise':
                next_url = f"/exercise-app/exercise-selectable/{patient.id}/"
            elif redirectTarget == 'return':
                if clinic_id:
                    next_url = reverse('assigned-clinic-dashboard', args=[clinic_id])
                else:
                    next_url = reverse('personal-dashboard')
            else:
                # If a custom URL is provided directly
                next_url = redirectTarget
            
            # Create TreatmentSession
            session = TreatmentSession.objects.create(
                patient=patient,
                session_number=data['session_number'],
                pre_pain=data.get('pre_pain'),
                pre_bp=data.get('pre_bp'),
                pre_hr=data.get('pre_hr'),
                pre_notes=data.get('pre_notes'),
                post_pain=data.get('post_pain'),
                treatment_response=data.get('treatment_response'),
                post_remarks=data.get('post_remarks'),
                follow_up_instructions=data.get('follow_up_instructions'),
                next_session=next_session,
                session_note=data.get('session_note', ''),
            )
            
            # Create modality junction records
            for mod_data in modalities_data:
                modality_name = mod_data['name']
                params = mod_data.get('params', {})
                # Get or create Modality (by name)
                modality, _ = Modality.objects.get_or_create(name=modality_name)
                # Create junction
                TreatmentSessionModality.objects.create(
                    session=session,
                    modality=modality,
                    parameters=params
                )
        
        # # Return success response
        # # next_url = f"/personal-acc/assigned-clinic-dashboard/{clinic_id}/"
        # next_url = f"/exercise-app/exercise-selectable/{patient.id}/"
        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'next_url': next_url
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON payload'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})