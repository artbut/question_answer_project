# question_answer_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django_ckeditor_5 import views as ckeditor_5_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('qa_app.urls')),

    # CKEditor 5 file upload URL
    path('ckeditor5/upload/', ckeditor_5_views.upload_file, name='ck_editor_5_upload_file'),
]

# Для медиа файлов в разработке
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)