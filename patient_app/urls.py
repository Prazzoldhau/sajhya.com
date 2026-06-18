from django.urls import path
from . import views


urlpatterns = [
    path ('patient-login/', views.patient_login, name = "patient-login"),
    path ('patient-dashboard/', views.patient_dashboard, name = "patient-dashboard"),
    
]
