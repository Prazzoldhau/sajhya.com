from django.urls import path
from .import views

urlpatterns = [
   path ('exercise-selectable/<int:patient_id>/', views.load_exercises, name='exercise-selectable'),
   path ('api/get-exercises/', views.get_exercises_by_subregion, name='get_exercises'),
   path ('api/submit-prescription/', views.submit_prescription, name="submit-prescription"),
   path ('prescription-exercise-details/', views.prescription_exercise_details, name = "prescription-exercise-details"),
   path ('prescriptipn/<int:patient_id>/', views.patient_prescriptions_view, name='patient_prescriptions'),
   path ('session-details/', views.session_detail, name="session-details"),
   path ('edit-reassign-exercise/<int:patient_id>/', views.add_edit_exercise, name="add-edit-exercise"),
]


