from django.db import models, IntegrityError, transaction
from django.conf import settings
import secrets, string,pytz
from datetime import datetime
from clinic_account.models import Clinic
from django.db import models
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from qrcode import make as make_qr
from io import BytesIO

def get_nepal_time():
    tz = pytz.timezone('Asia/Kathmandu')
    return datetime.now(tz)


class AddPatient(models.Model):
    patient_code = models.CharField(max_length=14, editable=False, unique=True)
    patient_name = models.CharField(max_length=50)
    patient_contact = models.CharField(max_length=50)
    completed_session = models.IntegerField(default=0)
    patient_diagnosis = models.CharField(max_length=100)
    qr_code = models.URLField(blank=True, null=True)  # store the image URL
    qr_token = models.CharField(max_length=32,null=True, editable=False, unique=True, blank=True)
        
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
        prefix = "PAT-"
        length = 6  # shorter than 10 for readability; adjust as needed
        alphabet = string.ascii_uppercase + string.digits
        while True:
            random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
            code = prefix + random_part
            if not AddPatient.objects.filter(patient_code=code).exists():
                return code
    def generate_qr_token(self):
        return secrets.token_urlsafe(24)

    def generate_qr_code(self):
        raw_data = self.qr_token
        qr_img = make_qr(raw_data)
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        buffer.seek(0)

        filename = f"qr_codes/{self.patient_code}.png"
        path = default_storage.save(filename, ContentFile(buffer.read()))
        return default_storage.url(path)

    def save(self, *args, **kwargs):
        if not self.patient_code:
            self.patient_code = self.generate_patient_code()
        if not self.qr_token:
            self.qr_token = self.generate_qr_token()
        if not self.qr_code:
            self.qr_code = self.generate_qr_code()
        
        try:
            with transaction.atomic():
                super().save(*args, **kwargs)
        except IntegrityError:
            self.patient_code = self.generate_patient_code()
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient_name} ({self.patient_code})"
    
    
