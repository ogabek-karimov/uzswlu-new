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
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'apps.core',
    'apps.accounts',
    'apps.content',
    'apps.structure',
    'apps.pages',
    'apps.hemis',
    'apps.api',
    'apps.panel',
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

# Payload CMS'dan ko'chirilgan parollar User.legacy_password'da — birinchi kirishda standart usulga o'tkaziladi
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend', 'apps.accounts.backends.LegacyPasswordBackend']

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
    'DEFAULT_SCHEMA_CLASS': 'apps.api.schema.TaggedAutoSchema',
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
# HEMIS: API manzili va tokeni berilsa — haqiqiy ma'lumot (har kuni `manage.py sync_hemis` bilan bazaga olinadi),
# berilmasa — namuna (seed_data/hemis-snapshot.json). Kodda boshqa hech narsa o'zgarmaydi.
HEMIS_API_URL = env('HEMIS_API_URL').rstrip('/')          # masalan: https://hemis.uzswlu.uz/rest/v1
HEMIS_API_TOKEN = env('HEMIS_API_TOKEN')
HEMIS_TIMEOUT = int(env('HEMIS_TIMEOUT', '20'))
HEMIS_CLIENT = env('HEMIS_CLIENT', 'apps.hemis.cache.CachedHemis' if HEMIS_API_URL else 'apps.hemis.snapshot.SnapshotHemis')
# HEMIS orqali kirish (OAuth2): xodimlar admin panelga va o'z kabinetiga universitet login-paroli bilan kiradi
HEMIS_OAUTH_URL = env('HEMIS_OAUTH_URL').rstrip('/')      # masalan: https://hemis.uzswlu.uz
HEMIS_OAUTH_CLIENT_ID = env('HEMIS_OAUTH_CLIENT_ID')
HEMIS_OAUTH_CLIENT_SECRET = env('HEMIS_OAUTH_CLIENT_SECRET')
HEMIS_OAUTH_AUTHORIZE_PATH = env('HEMIS_OAUTH_AUTHORIZE_PATH', '/oauth/authorize')
HEMIS_OAUTH_TOKEN_PATH = env('HEMIS_OAUTH_TOKEN_PATH', '/oauth/access-token')
HEMIS_OAUTH_USER_PATH = env('HEMIS_OAUTH_USER_PATH', '/oauth/api/user')
HEMIS_OAUTH_ENABLED = bool(HEMIS_OAUTH_URL and HEMIS_OAUTH_CLIENT_ID and HEMIS_OAUTH_CLIENT_SECRET)
ADMIN_PANEL_URL = env('ADMIN_PANEL_URL', 'http://localhost:5173').rstrip('/')
SITE_URL = env('SITE_URL', 'http://localhost:3000').rstrip('/')

# Swagger / OpenAPI hujjati: /api/docs/ (Swagger UI), /api/redoc/, /api/schema/
API_DOCS_PUBLIC = env_bool('API_DOCS_PUBLIC', DEBUG)
SPECTACULAR_SETTINGS = {
    'TITLE': 'ÖzDJTU sayti — API',
    'DESCRIPTION': (
        'Sayt (Nuxt) uchun ochiq API, Vue admin panel API’si (/api/cms/*) va xodim kabineti. '
        'Barcha matnlar `?lang=uz|ru|en|zh` bo‘yicha qaytadi. Admin panel kirishi — /api/cms/users/login (sessiya cookie).'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'OAS_VERSION': '3.1.0',
    'POSTPROCESSING_HOOKS': ['drf_spectacular.hooks.postprocess_schema_enums', 'apps.api.swagger.merge_contract'],
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    'SCHEMA_PATH_PREFIX': r'/api',
    'COMPONENT_SPLIT_REQUEST': True,
    'DISABLE_ERRORS_AND_WARNINGS': True,
    'SWAGGER_UI_SETTINGS': {'persistAuthorization': True, 'docExpansion': 'none', 'filter': True},
    'TAGS': [
        {'name': 'Sayt API', 'description': 'frontend/docs/openapi.yaml shartnomasi: bosh sahifa, postlar, sahifalar, tuzilma, BRM …'},
        {'name': 'Sayt (Payload mos)', 'description': 'NUXT_CMS_BASE=<backend>/api/site bilan ishlash uchun eski manzillar'},
        {'name': 'Xodim kabineti', 'description': 'HEMIS orqali kirgan xodim: profil, hujjatlar'},
        {'name': 'HEMIS', 'description': 'HEMIS bilan ulanish: kirish (OAuth2) va holat'},
        {'name': 'Admin panel: kirish'}, {'name': 'Admin panel: kolleksiyalar'}, {'name': 'Admin panel: globallar'},
        {'name': 'Admin panel: versiyalar'}, {'name': 'Admin panel: yig‘ma ma’lumot'},
    ],
}
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
        {'name': 'API hujjati (Swagger)', 'url': '/api/docs/', 'new_window': True},
        {'name': 'Admin panel (Vue)', 'url': ADMIN_PANEL_URL, 'new_window': True},
        {'name': 'Sayt', 'url': SITE_URL, 'new_window': True},
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
