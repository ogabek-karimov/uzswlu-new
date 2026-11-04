"""ÖzDJTU sayti — backend (Django + DRF) sozlamalari. Hamma narsa .env orqali boshqariladi."""
import os
from pathlib import Path
from urllib.parse import unquote, urlparse

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name: str, default: str = '') -> str:
    return os.environ.get(name, default)


def env_bool(name: str, default: bool = False) -> bool:
    return env(name, 'true' if default else 'false').strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(name: str, default: str = '') -> list[str]:
    return [v.strip() for v in env(name, default).split(',') if v.strip()]


DEBUG = env_bool('DEBUG', False)
SECRET_KEY = env('SECRET_KEY') or ('dev-insecure-key-change-me' if DEBUG else '')
if not SECRET_KEY:
    raise RuntimeError('SECRET_KEY .env faylida yo‘q')

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', 'localhost,127.0.0.1')

# Backend'ning tashqi manzili: rasm va fayl havolalari to'liq URL bo'lishi shart (frontend boshqa domenda)
PUBLIC_SERVER_URL = env('PUBLIC_SERVER_URL', 'http://localhost:8000').rstrip('/')
# Cookie bilan so'rov yubora oladigan manzillar: sayt va admin panel
TRUSTED_ORIGINS = env_list('TRUSTED_ORIGINS', 'http://localhost:5173,http://localhost:3000')

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'apps.core',
    'apps.accounts',
    'apps.content',
    'apps.structure',
    'apps.pages',
    'apps.hemis',
    'apps.api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]


def _database() -> dict:
    url = urlparse(env('DATABASE_URL', 'postgres://uzswlu:uzswlu@localhost:5432/uzswlu'))
    if url.scheme == 'sqlite':  # tezkor lokal tekshiruv uchun: DATABASE_URL=sqlite:///db.sqlite3
        return {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / (url.path.lstrip('/') or 'db.sqlite3')}
    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': url.path.lstrip('/'),
        'USER': unquote(url.username or ''),
        'PASSWORD': unquote(url.password or ''),
        'HOST': url.hostname or 'localhost',
        'PORT': str(url.port or 5432),
        'CONN_MAX_AGE': 60,
    }


DATABASES = {'default': _database()}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
]

LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    # Manifest'siz: Jazzmin CSS'idagi havolalar collectstatic'ni buzmasligi uchun
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}
SERVE_MEDIA = env_bool('SERVE_MEDIA', True)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DATA_UPLOAD_MAX_MEMORY_SIZE = 60 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

# --- CORS / CSRF ---
CORS_ALLOWED_ORIGINS = TRUSTED_ORIGINS
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = TRUSTED_ORIGINS + ([PUBLIC_SERVER_URL] if PUBLIC_SERVER_URL.startswith('http') else [])

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = env_bool('COOKIE_SECURE', True)
    CSRF_COOKIE_SECURE = env_bool('COOKIE_SECURE', True)
    SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_AGE = 60 * 60 * 12

# --- DRF ---
REST_FRAMEWORK = {
    # Autentifikatsiya har bir view'da alohida (ochiq API — token, kabinet — xodim sessiyasi)
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_THROTTLE_RATES': {'appeals': '60/hour', 'hit': '120/minute', 'cabinet-upload': '30/hour'},
    'UNAUTHENTICATED_USER': None,
    # Nginx/Cloudflare ortida nechta proksi bo'lsa shuncha (so'rov cheklovlari haqiqiy IP bo'yicha ishlashi uchun)
    'NUM_PROXIES': int(env('NUM_PROXIES', '0')),
}

# --- Sayt (frontend) bilan shartnoma ---
# Ochiq API tokeni (frontend serverida NUXT_API_TOKEN). Bo'sh bo'lsa — tekshirilmaydi.
API_TOKEN = env('API_TOKEN')
# Xodim kabineti sessiyasi: cookie nomi va amal qilish muddati
STAFF_SESSION_COOKIE = env('STAFF_SESSION_COOKIE', 'session')
STAFF_SESSION_TTL_HOURS = int(env('STAFF_SESSION_TTL_HOURS', '12'))
# Tarjimasi yo'q postlar boshqa tillardagi ro'yxatda chiqmasin (admin panel qoidasi). False — o'zbekchasi bilan chiqadi.
HIDE_UNTRANSLATED_POSTS = env_bool('HIDE_UNTRANSLATED_POSTS', True)
# Nuxt keshini yangilash (ixtiyoriy)
SITE_PURGE_URL = env('SITE_PURGE_URL')
SITE_PURGE_TOKEN = env('SITE_PURGE_TOKEN')
# HEMIS klienti: hozircha namuna (snapshot); haqiqiy API ulanganda shu yerga klass yo'li yoziladi
HEMIS_CLIENT = env('HEMIS_CLIENT', 'apps.hemis.snapshot.SnapshotHemis')
HEMIS_SNAPSHOT = env('HEMIS_SNAPSHOT', str(BASE_DIR / 'seed_data' / 'hemis-snapshot.json'))

LOGIN_URL = '/admin/login/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': env('LOG_LEVEL', 'INFO')},
}

# --- Jazzmin (admin panel) ---
JAZZMIN_SETTINGS = {
    'site_title': 'ÖzDJTU admin',
    'site_header': 'ÖzDJTU',
    'site_brand': 'ÖzDJTU',
    'welcome_sign': 'ÖzDJTU saytini boshqarish',
    'copyright': 'ÖzDJTU',
    'search_model': ['content.Post', 'pages.Page'],
    'user_avatar': None,
    'topmenu_links': [
        {'name': 'Bosh sahifa', 'url': 'admin:index'},
    ],
    'show_sidebar': True,
    'navigation_expanded': False,
    'order_with_respect_to': [
        'content', 'pages', 'structure', 'core', 'accounts',
    ],
    'icons': {
        'accounts.User': 'fas fa-user-shield',
        'content.Post': 'fas fa-newspaper',
        'content.Category': 'fas fa-tags',
        'content.Slide': 'fas fa-images',
        'content.Leader': 'fas fa-user-tie',
        'content.Document': 'fas fa-file-pdf',
        'content.DocCategory': 'fas fa-folder',
        'content.Video': 'fas fa-video',
        'content.VideoCategory': 'fas fa-film',
        'content.VideoPage': 'fas fa-broadcast-tower',
        'content.StateSymbol': 'fas fa-flag',
        'content.Partner': 'fas fa-handshake',
        'content.TaughtLanguage': 'fas fa-language',
        'pages.Page': 'fas fa-sitemap',
        'pages.SdgGoal': 'fas fa-globe',
        'pages.SdgPage': 'fas fa-leaf',
        'structure.Faculty': 'fas fa-university',
        'structure.Department': 'fas fa-building',
        'structure.StaffProfile': 'fas fa-id-card',
        'structure.Program': 'fas fa-graduation-cap',
        'structure.AdmissionSettings': 'fas fa-door-open',
        'structure.Campus': 'fas fa-map-marker-alt',
        'structure.Appeal': 'fas fa-inbox',
        'core.Media': 'fas fa-photo-video',
        'core.SiteSettings': 'fas fa-cogs',
        'core.Activity': 'fas fa-history',
        'core.Hit': 'fas fa-chart-line',
    },
    'default_icon_parents': 'fas fa-folder',
    'default_icon_children': 'fas fa-circle',
    'related_modal_active': False,
    'changeform_format': 'horizontal_tabs',
}
JAZZMIN_UI_TWEAKS = {'theme': 'flatly', 'navbar_small_text': True, 'sidebar_nav_small_text': True}
