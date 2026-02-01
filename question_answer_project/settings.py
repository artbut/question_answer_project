import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-your-secret-key-here')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_ckeditor_5',

    # Local apps
    'qa_app.apps.QaAppConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'question_answer_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'qa_app.context_processors.sidebar_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'question_answer_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login/Logout URLs
LOGIN_URL = 'qa_app:login'
LOGIN_REDIRECT_URL = 'qa_app:home'
LOGOUT_REDIRECT_URL = 'qa_app:home'

CKEDITOR_5_CONFIGS = {
    'extends': {
        'toolbar': {
            'items': [
                'heading', '|',
                'bold', 'italic', 'underline', 'strikethrough', '|',
                'fontSize', 'fontFamily', 'fontColor', 'fontBackgroundColor', '|',
                'alignment', '|',
                'bulletedList', 'numberedList', 'todoList', '|',
                'link', 'imageUpload', 'mediaEmbed', 'blockQuote', 'insertTable', '|',
                'undo', 'redo', 'sourceEditing', '|',
                'code', 'codeBlock', 'horizontalLine', 'pageBreak'
            ],
            'shouldNotGroupWhenFull': True
        },
        'image': {
            'toolbar': [
                'imageTextAlternative', 'toggleImageCaption',
                'imageStyle:inline', 'imageStyle:wrapText', 'imageStyle:breakText',
                '|', 'imageStyle:alignLeft', 'imageStyle:alignRight', 'imageStyle:alignCenter'
            ],
            'styles': ['full', 'side', 'alignLeft', 'alignRight', 'alignCenter']
        },
        'upload': {
            'maxFileSize': 5242880,  # 5 MB
        },
        'table': {
            'contentToolbar': [
                'tableColumn', 'tableRow', 'mergeTableCells',
                'tableProperties', 'tableCellProperties'
            ]
        },
        'heading': {
            'options': [
                {'model': 'paragraph', 'title': 'Paragraph', 'class': 'ck-heading_paragraph'},
                {'model': 'heading1', 'view': 'h1', 'title': 'Heading 1', 'class': 'ck-heading_heading1'},
                {'model': 'heading2', 'view': 'h2', 'title': 'Heading 2', 'class': 'ck-heading_heading2'},
                {'model': 'heading3', 'view': 'h3', 'title': 'Heading 3', 'class': 'ck-heading_heading3'},
                {'model': 'heading4', 'view': 'h4', 'title': 'Heading 4', 'class': 'ck-heading_heading4'}
            ]
        },
        'language': 'ru',  # Русский интерфейс
        'height': '400px',  # Высота редактора
        'width': '100%',  # Ширина редактора
    }
}

# Настройки загрузки файлов для CKEditor 5
CKEDITOR_5_FILE_UPLOAD_PERMISSION = "staff"  # "staff" или "authenticated"
CKEDITOR_5_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
CKEDITOR_5_ALLOW_ALL_FILE_TYPES = False
CKEDITOR_5_UPLOAD_FILE_TYPES = ['jpeg', 'jpg', 'png', 'gif', 'bmp', 'webp', 'svg']

# Если нужно ограничить загрузку файлов по пользователям
CKEDITOR_5_RESTRICT_BY_USER = True  # Аналог старого CKEDITOR_RESTRICT_BY_USER

# Показывать директории при просмотре
CKEDITOR_5_BROWSE_SHOW_DIRS = True  # Аналог CKEDITOR_BROWSE_SHOW_DIRS

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
