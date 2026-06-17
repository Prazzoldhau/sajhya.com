from django.db import models
from personal_account.models import AddPatient
# Create your models here.
from django.db import models



class TreatmentSession(models.Model):
    # PROGRESS_CHOICES = [
    #     ('much_worse', 'Much worse'),
    #     ('worse', 'Worse'),
    #     ('same', 'Same'),
    #     ('better', 'Better'),
    #     ('much_better', 'Much better'),
    # ]
    
    patient = models.ForeignKey(AddPatient, on_delete=models.CASCADE, related_name='sessions')
    session_number = models.PositiveIntegerField(default=0)

    session_date = models.DateTimeField(auto_now_add=True)  # auto set when created

    
    # Pre‑session assessment
    # pre_pain = models.PositiveSmallIntegerField(blank=True, null=True)  # 0‑10 # remove
    # pre_bp = models.CharField(max_length=20, blank=True, null=True)     # "120/80" #remove
    # pre_hr = models.PositiveSmallIntegerField(blank=True, null=True)    # heart rate #remove
    pre_notes = models.TextField(blank=True, null=True) #remove
    # progress_status = models.CharField(max_length=20, choices=PROGRESS_CHOICES, blank=True, null=True) #remove
    
    # Post‑session assessment
    # post_pain = models.PositiveSmallIntegerField(blank=True, null=True) # remove
    
    treatment_response = models.CharField(max_length=20, blank=True, null=True)  # "excellent", "good", etc.
    # post_remarks = models.TextField(blank=True, null=True)
    
    # Follow‑up
    # follow_up_instructions = models.TextField(blank=True, null=True)#remove
    # next_session = models.DateField(blank=True, null=True)#remove
    
    # Session notes (general)
    session_note = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['patient', 'session_number']  # each patient has unique session numbers
        ordering = ['-session_date']
    
    def __str__(self):
        return f"Session {self.session_number} - {self.patient.patient_name}"

class Modality(models.Model):
    """Predefined list of modalities (e.g., IFT, TENS, Ultrasound)"""
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, blank=True, null=True)  # electro, manual, etc.
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class TreatmentSessionModality(models.Model):
    """Many‑to‑many through table to store parameters for each modality used in a session"""
    session = models.ForeignKey(TreatmentSession, on_delete=models.CASCADE, related_name='selected_modalities')
    modality = models.ForeignKey(Modality, on_delete=models.CASCADE)
    parameters = models.JSONField(default=dict)  # stores all key‑value pairs like {"frequency":"4000 Hz", "duration":10}
    
    class Meta:
        unique_together = ['session', 'modality']
    
    def __str__(self):
        return f"{self.modality.name} in {self.session}"