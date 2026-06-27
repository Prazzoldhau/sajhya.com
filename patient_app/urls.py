from django.urls import path
from . import views


urlpatterns = [
    path ('patient-login/', views.patient_login, name = "patient-login"),
    path ('patient-dashboard/', views.patient_dashboard, name = "patient-dashboard"),
    path ('api/login/', views.patient_api_login, name='patient_api_login'),# ✅ NEW: Mobile API endpoint (JSON)
    path ('api/qr-login/', views.patient_api_qr_login, name='patient_api_qr_login'),# ✅ NEW: QR login (JSON)
    path ('api/csrf/', views.csrf_token_view, name='csrf_token'),
    path ('api/me/', views.patient_api_me, name='patient_api_me'),  # ✅ NEW
    path ('api/logout/', views.patient_api_logout, name='patient_api_logout'),  # ✅ NEW
]
