from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path ('', TemplateView.as_view(template_name="index.html"), name='landing'),
    path ('admin/', admin.site.urls),
    path ('', include('main.urls')),
    path ('acc/', include ('account_app.urls')),
    path ('personal-acc/', include ('personal_account.urls')),
    path ('clinic-acc/', include('clinic_account.urls')),
    path ('exercise-app/', include('exercise_app.urls')),
    path ('detail-app/', include('detail_app.urls')),
    path ('video-app/', include('video_app.urls')),
    path ('prescription-app/', include('prescription_app.urls')),
    path ('patient-app/', include('patient_app.urls')),

]

# Only serve media files in development (DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)