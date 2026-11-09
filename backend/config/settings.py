"""ÖzDJTU sayti — backend (Django + DRF) sozlamalari. Hamma narsa .env orqali boshqariladi."""
import os
from pathlib import Path
from urllib.parse import unquote, urlparse

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    """Lokal ishga tushirishda (`python manage.py runserver`) .env ni o'qiydi. Docker/serverda
    o'zgaruvchilar allaqachon berilgan bo'ladi — ular hech qachon ustidan yozilmaydi.
    SKIP_DOTENV=1 bo'lsa umuman o'qilmaydi (testlar hermetik bo'lishi uchun — `config/settings_test.py`)."""
    if os.environ.get('SKIP_DOTENV') == '1':
        return
    for path in (BASE_DIR / '.env', BASE_DIR.parent / '.env'):
        if not path.is_file():
            continue
        for raw in path.read_text(encoding='utf-8-sig').splitlines():
            line = raw.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
                value = value[1:-1]
            os.environ.setdefault(key.strip(), value)


_load_dotenv()


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
JWT_TTL_SECONDS = int(env('JWT_TTL_SECONDS', str(8 * 3600)))  # admin panel JWT amal qilish muddati (soniya)
TRUSTED_ORIGINS = env_list('TRUSTED_ORIGINS', 'http://localhost:5173,http://localhost:3000')
# localhost va 127.0.0.1 bitta kompyuter: admin panelni qaysi biri bilan ochsangiz ham yozish so'rovlari rad etilmasin
TRUSTED_ORIGINS += [o.replace('//localhost', '//127.0.0.1') for o in TRUSTED_ORIGINS if '//localhost' in o and o.replace('//localhost', '//127.0.0.1') not in TRUSTED_ORIGINS]

INSTALLED_APPS = [
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
    'apps.core.middleware.UploadSizeLimitMiddleware',
    'apps.core.middleware.MediaHeadersMiddleware',
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
        name = url.path.lstrip('/') or 'db.sqlite3'
        # `sqlite:///:memory:` — haqiqiy xotiradagi baza (fayl yaratilmaydi); boshqasi BASE_DIR ga nisbatan
        return {'ENGINE': 'django.db.backends.sqlite3', 'NAME': name if name == ':memory:' else BASE_DIR / name}
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
    # Manifest'siz: Swagger UI fayllari uchun oddiy siqilgan saqlash
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}
SERVE_MEDIA = env_bool('SERVE_MEDIA', True)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
# Ochiq berilmaydigan fayllar (murojaat ilovalari). Faqat superadmin autentifikatsiya bilan yuklab oladi. Serverda alohida volume bo'lsin.
PRIVATE_ROOT = Path(env('PRIVATE_ROOT', str(BASE_DIR / 'private')))
# Yuklash so'rovining eng katta hajmi (bayt): fayl o'qilishidan OLDIN rad etiladi (prefiks → limit)
UPLOAD_LIMITS = [
    ('/api/appeals', 12 * 1024 * 1024),
    ('/api/me/', 22 * 1024 * 1024),
    ('/api/cms/', 55 * 1024 * 1024),
]
DATA_UPLOAD_MAX_MEMORY_SIZE = 60 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 500       # ko'p maydonli (query/form) so'rov bilan xotirani to'ldirishga qarshi
DATA_UPLOAD_MAX_NUMBER_FILES = 20
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
    SECURE_HSTS_SECONDS = int(env('HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_REFERRER_POLICY = 'same-origin'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
X_FRAME_OPTIONS = 'DENY'

# --- Kesh (so'rov cheklovlari hisobi + ochiq API javoblari). REDIS_URL bo'lsa — Redis, bo'lmasa fayl (jarayonlar orasida umumiy) ---
if env('REDIS_URL'):
    CACHES = {'default': {'BACKEND': 'django.core.cache.backends.redis.RedisCache', 'LOCATION': env('REDIS_URL')}}
else:
    CACHES = {'default': {'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache', 'LOCATION': env('CACHE_DIR', '/tmp/uzswlu-cache'), 'OPTIONS': {'MAX_ENTRIES': 5000}}}
PUBLIC_CACHE_SECONDS = int(env('PUBLIC_CACHE_SECONDS', '60'))   # ochiq GET javoblari keshi (0 — o'chirilgan); kontent o'zgarsa darhol yangilanadi
HEMIS_CACHE_SECONDS = int(env('HEMIS_CACHE_SECONDS', '300'))    # HEMIS nusxasini bazadan qayta o'qish oralig'i
ADMIN_MAX_LIMIT = int(env('ADMIN_MAX_LIMIT', '5000'))           # admin ro'yxatida bir so'rovda ko'pi bilan
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
    # So'rov cheklovlari (apps/core/throttles.py). Qiymatlar .env orqali o'zgartiriladi: THROTTLE_LOGIN=10/min
    'DEFAULT_THROTTLE_RATES': {
        'public': env('THROTTLE_PUBLIC', '300/min'),        # ochiq API (API_TOKEN'siz yoki noto'g'ri token bilan), IP bo'yicha
        'open': env('THROTTLE_OPEN', '1200/min'),           # tokensiz ochiq manzillar (/api/site/*), IP bo'yicha
        'search': env('THROTTLE_SEARCH', '40/min'),         # qidiruv og'ir — alohida
        'login': env('THROTTLE_LOGIN', '10/min'),           # admin kirish/yangilash: parol terib ko'rishga qarshi, IP bo'yicha
        'hemis-auth': env('THROTTLE_HEMIS_AUTH', '20/min'), # HEMIS OAuth: HEMIS serveriga ortiqcha so'rov ketmasin
        'panel-read': env('THROTTLE_PANEL_READ', '1200/min'),
        'panel-write': env('THROTTLE_PANEL_WRITE', '180/min'),
        'cabinet': env('THROTTLE_CABINET', '180/min'),
        'cabinet-upload': env('THROTTLE_CABINET_UPLOAD', '30/hour'),
        'appeals': env('THROTTLE_APPEALS', '20/hour'),
        'hit': env('THROTTLE_HIT', '240/min'),
        'docs': env('THROTTLE_DOCS', '60/min'),
    },
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_SCHEMA_CLASS': 'apps.api.schema.TaggedAutoSchema',
    # Nginx/Cloudflare ortida nechta proksi bo'lsa shuncha (so'rov cheklovlari haqiqiy IP bo'yicha ishlashi uchun)
    'NUM_PROXIES': int(env('NUM_PROXIES', '0')),
}

# --- Sayt (frontend) bilan shartnoma ---
# Ochiq API tokeni (frontend serverida NUXT_API_TOKEN). Bo'sh bo'lsa — tekshirilmaydi.
API_TOKEN = env('API_TOKEN')
# 2FA (TOTP) majburiy rollar, vergul bilan: REQUIRE_2FA_ROLES=superadmin,editor. Bo'sh — hamma uchun ixtiyoriy
REQUIRE_2FA_ROLES = env_list('REQUIRE_2FA_ROLES', '')
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
HEMIS_TIMEOUT = int(env('HEMIS_TIMEOUT', '20'))            # sinxronlash (fon jarayoni) uchun
HEMIS_OAUTH_TIMEOUT = int(env('HEMIS_OAUTH_TIMEOUT', '8'))  # kirish paytida foydalanuvchi kutadi — qisqa
HEMIS_REQUEST_DELAY = float(env('HEMIS_REQUEST_DELAY', '0.2'))  # sinxronlashda sahifalar orasida pauza (HEMIS'ga bosim tushmasin)
# Og'ir ishlar KECHASI (server ham, HEMIS ham bo'sh): jadval `manage.py run_nightly` (alohida konteyner), cron/Celery shart emas.
HEMIS_SYNC_WINDOW = env('HEMIS_SYNC_WINDOW', '01:00-05:00')       # HEMIS'ga faqat shu oynada chiqiladi (mahalliy vaqt, TIME_ZONE)
HEMIS_SYNC_AT = env('HEMIS_SYNC_AT', '02:30')                     # har kuni shu vaqtdan boshlab (+ tasodifiy kechikish)
HEMIS_SYNC_JITTER_MINUTES = int(env('HEMIS_SYNC_JITTER_MINUTES', '20'))
HEMIS_MAX_REQUESTS = int(env('HEMIS_MAX_REQUESTS', '3000'))       # bitta sinxronlashda HEMIS'ga ko'pi bilan shuncha so'rov
HEMIS_MAX_CONSECUTIVE_FAILURES = int(env('HEMIS_MAX_CONSECUTIVE_FAILURES', '5'))  # ketma-ket xato — sinxronlash to'xtaydi (HEMIS'ni bosmaymiz)
HEMIS_OAUTH_GLOBAL_PER_MIN = int(env('HEMIS_OAUTH_GLOBAL_PER_MIN', '120'))  # HEMIS orqali kirish: hamma IP'lar uchun umumiy chegara
LOGIN_EVENT_RETENTION_DAYS = int(env('LOGIN_EVENT_RETENTION_DAYS', '365'))  # kirish tarixi shuncha kun saqlanadi (0 — o'chirmaydi)
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
SWAGGER_THEME = env('SWAGGER_THEME', 'modern')  # modern | classic
SPECTACULAR_SETTINGS = {
    'TITLE': 'ÖzDJTU sayti — API',
    'DESCRIPTION': 'ÖzDJTU API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'OAS_VERSION': '3.1.0',
    'POSTPROCESSING_HOOKS': ['drf_spectacular.hooks.postprocess_schema_enums', 'apps.api.swagger.merge_contract', 'apps.api.swagger.finalize'],
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    'SCHEMA_PATH_PREFIX': r'/api',
    'COMPONENT_SPLIT_REQUEST': True,
    'DISABLE_ERRORS_AND_WARNINGS': True,
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True, 'docExpansion': 'none', 'filter': True, 'deepLinking': True,
        'layout': 'BaseLayout', 'defaultModelsExpandDepth': -1, 'defaultModelExpandDepth': 2,
        'tryItOutEnabled': True, 'displayRequestDuration': True,
    },
}
HEMIS_SNAPSHOT = env('HEMIS_SNAPSHOT', str(BASE_DIR / 'seed_data' / 'hemis-snapshot.json'))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': env('LOG_LEVEL', 'INFO')},
}
