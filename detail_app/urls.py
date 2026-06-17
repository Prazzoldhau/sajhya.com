from django.urls import path
from .import views


urlpatterns = [
    path ('patient-detail/<int:patient_id>/', views.patient_detail, name = "patient-detail"),
    path ('patient-exericse-status/<int:patient_id>/', views.patient_exercise_status, name="patient-exercise-status"),
    path ('api/exercise/<int:exercise_id>/toggle-completion/', views.toggle_exercise_completion, name='toggle_exercise_completion'),
    path ('reassign-exercise/<int:patient_id>/latest-prescription/', views.latest_prescription, name='api-latest-prescription'),
]
