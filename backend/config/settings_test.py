"""Test sozlamalari — `python manage.py test` avtomatik shuni ishlatadi (manage.py).

Maqsad: testlar (1) hermetik — lokal .env ga bog'liq emas, (2) tez, (3) bir-birini buzmaydi va parallel (`--parallel`) ishlaydi:
  - .env o'qilmaydi; kerakli qiymatlar shu yerda qat'iy beriladi;
  - baza — xotiradagi SQLite; kesh — jarayon ichidagi (locmem);
  - parol xeshi — tez MD5 (faqat testda; PBKDF2 har loginda sekin);
  - MEDIA_ROOT / PRIVATE_ROOT — vaqtinchalik papka (chiqishda o'chiriladi), haqiqiy fayllarga tegilmaydi.
"""
import atexit
import os
import shutil
import tempfile

os.environ['SKIP_DOTENV'] = '1'
for key, value in {
    'DEBUG': '1',
    'SECRET_KEY': 'test-only-secret-key-not-for-production-0123456789',
    # Standart — xotiradagi SQLite. CI'da PostgreSQL bilan ham sinash uchun: TEST_DATABASE_URL=postgres://...
    'DATABASE_URL': os.environ.get('TEST_DATABASE_URL') or 'sqlite:///:memory:',
    'SUPERADMIN_PASSWORD': 'Str0ng!Pass#2026-test',   # seed_demo superadmin yaratishi uchun
    'API_TOKEN': '',
    'API_DOCS_PUBLIC': 'true',
    'REQUIRE_2FA_ROLES': '',
    'REDIS_URL': '',
    'HEMIS_API_URL': '',
    'BACKUP_ENABLED': '0',   # testlar o'zi yoqadi (tests/core/test_backup.py)
    'NUM_PROXIES': '0',
}.items():
    os.environ[key] = value

from .settings import *  # noqa: E402,F403

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'uzswlu-tests'}}

_TMP = tempfile.mkdtemp(prefix='uzswlu-test-')
atexit.register(shutil.rmtree, _TMP, ignore_errors=True)
BACKUP_DIR = os.path.join(_TMP, 'backups')
MEDIA_ROOT = os.path.join(_TMP, 'media')
PRIVATE_ROOT = os.path.join(_TMP, 'private')
os.makedirs(MEDIA_ROOT, exist_ok=True)
os.makedirs(PRIVATE_ROOT, exist_ok=True)
