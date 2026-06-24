from django.urls import path
from . import views

urlpatterns = [
    path ('upload-apk/', views.upload_apk, name = "upload-apk"),
    path ('upload-page/', views.upload_page, name='upload_page'),  # 🔥 NEW: The frontend page
    path ('download-apk/', views.download_latest_app, name='download_app'),
    path ('download-page/', views.app_download_page, name = "app-download-page"),
]
