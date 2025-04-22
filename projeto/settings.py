from django.contrib.messages import constants as messages
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-psfjm1^5@(u7z5%!4sc+kpg^&2$8o0i1(_!)&t)wgb1%3*gd=f'

DEBUG = False

CSRF_TRUSTED_ORIGINS = [
    'https://almoxerifado.onrender.com',
]

# settings.py
ALLOWED_HOSTS = ['almoxerifado.onrender.com', 'localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts.apps.accountsConfig',
    'suprimentos',
    'estoque',
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

ROOT_URLCONF = 'projeto.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'Templates'),  # Verifique se o caminho está correto
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'projeto.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sig_pzgt',
        'USER': 'root',
        'PASSWORD': '5LzH7l5gGDOBxSTt9aUpOlwWpYErNzZM',
        'HOST': 'dpg-d03u09ngi27c738d997g-a.oregon-postgres.render.com',
        'PORT': '5432',
    }
}

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

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'

STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'public/static'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGOUT_REDIRECT_URL = '/accounts/login'
LOGIN_URL = '/accounts/login'
LOGIN_REDIRECT_URL = '/'


MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',

}

AUTH_USER_MODEL = 'accounts.CustomUser'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

DEBUG = True
