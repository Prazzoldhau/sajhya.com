from django.urls import path
from .import views

urlpatterns = [
    path ('prescription-page/<int:patient_id>', views.start_prescription, name="prescription-page"),
    path ('api/save-treatment-session/', views.save_treatment_session, name='save_treatment_session'),
]
