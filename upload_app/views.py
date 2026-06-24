from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt  # Only if testing; use @login_required in prod
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import default_storage
import os
import datetime

@staff_member_required  # Only staff/admin can upload
@csrf_exempt  # Remove this if you send CSRF token via frontend
def upload_apk(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    uploaded_file = request.FILES.get('apkFile')
    
    if not uploaded_file:
        return JsonResponse({'error': 'No file provided.'}, status=400)

    # Validation checks (same as DRF version)
    if uploaded_file.content_type != 'application/vnd.android.package-archive':
        return JsonResponse({'error': 'Only APK files allowed.'}, status=400)
    
    if not uploaded_file.name.endswith('.apk'):
        return JsonResponse({'error': 'File must have .apk extension.'}, status=400)

    if uploaded_file.size > 200 * 1024 * 1024:
        return JsonResponse({'error': 'File exceeds 200MB limit.'}, status=400)

    # Save with unique name
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    new_filename = f"app_{timestamp}.apk"
    relative_path = os.path.join('apks', new_filename)

    # Chunked writing
    file_path = default_storage.path(relative_path)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with default_storage.open(relative_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    return JsonResponse({
        'success': True,
        'message': 'APK uploaded successfully!',
        'fileName': new_filename,
        'filePath': relative_path,
        'fileSize': uploaded_file.size
    }, status=201)
    


@staff_member_required
def upload_page(request):
    # Only staff can see this page. If not staff, @staff_member_required redirects to login.
    return render(request, 'upload.html')

# medic/views.py
import os
from django.conf import settings
from django.shortcuts import render

def app_download_page(request):
    # Path to your APK file (inside MEDIA_ROOT/apps/)
    file_path = os.path.join(settings.MEDIA_ROOT, 'apps', 'patient_app.apk')
    file_exists = os.path.exists(file_path)
    
    # Optionally, read a version from a .txt file or hardcode it
    version = "1.0.0"  # You could store this in a separate file or model

    context = {
        'file_exists': file_exists,
        'version': version,
    }
    return render(request, 'download.html', context)



# medic/views.py (add this)
from django.http import FileResponse, Http404

def download_latest_app(request):
    file_path = os.path.join(settings.MEDIA_ROOT, 'apps', 'latest.apk')
    if not os.path.exists(file_path):
        raise Http404("App file not found.")
    response = FileResponse(open(file_path, 'rb'), as_attachment=True)
    response['Content-Disposition'] = 'attachment; filename="MyApp.apk"'
    return response
