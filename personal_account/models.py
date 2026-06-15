from django.db import models, IntegrityError, transaction
from django.conf import settings
import secrets
import string
import pytz
from datetime import datetime
from clinic_account.models import Clinic

def get_nepal_time():
    tz = pytz.timezone('Asia/Kathmandu')
    return datetime.now(tz)


class AddPatient(models.Model):
    patient_code = models.CharField(max_length=14, editable=False, unique=True)
    patient_name = models.CharField(max_length=50)
    patient_contact = models.CharField(max_length=50)
    completed_session = models.IntegerField(default=0)
    patient_diagnosis = models.CharField(max_length=100)
    
    # Foreign key points to the user who created the patient
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='physio_assigned'
    )
    
        # Foreign key points to the clinic where patient is created
    origin_clinic = models.ForeignKey(
        Clinic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clinic_assigned'
    )

    created_at = models.DateTimeField(default=get_nepal_time)
    def generate_patient_code(self):
        """Generate a unique patient code like PAT-A3F9K2"""
        prefix = "PAT-"
        length = 6  # shorter than 10 for readability; adjust as needed
        alphabet = string.ascii_uppercase + string.digits
        while True:
            random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
            code = prefix + random_part
            if not AddPatient.objects.filter(patient_code=code).exists():
                return code
    
    def save(self, *args, **kwargs):
        # Only generate a code if it doesn't already exist
        if not self.patient_code:
            self.patient_code = self.generate_patient_code()
            try:
                with transaction.atomic():
                    super().save(*args, **kwargs)
            except IntegrityError:
                # Very rare: another patient got the same code at the same microsecond
                self.patient_code = self.generate_patient_code()
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.patient_name} ({self.patient_code})"