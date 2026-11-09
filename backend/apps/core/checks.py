"""Ishga tushganda xavfsizlik sozlamalarini tekshiradi (`manage.py check`, gunicorn/Docker ishga tushishida chiqadi)."""
from django.conf import settings
from django.core.checks import Warning, register

WEAK_PASSWORDS = {'change-me-please', 'password', 'admin', 'admin123', 'superadmin', '12345678', 'qwerty123'}


@register()
def security_settings(app_configs, **kwargs):
    if settings.DEBUG:
        return []
    out = []
    tokens = [t.strip() for t in (settings.API_TOKEN or '').split(',') if t.strip()]
    if not tokens:
        out.append(Warning('API_TOKEN bo‘sh: ochiq API tokensiz hamma uchun ochiq.', hint='backend/.env da uzun tasodifiy API_TOKEN belgilang (frontendda NUXT_API_TOKEN bilan bir xil).', id='uzswlu.W001'))
    elif any(len(t) < 24 for t in tokens):
        out.append(Warning('API_TOKEN 24 belgidan qisqa.', hint='python -c "import secrets; print(secrets.token_urlsafe(32))"', id='uzswlu.W002'))
    if len(settings.SECRET_KEY) < 32 or settings.SECRET_KEY.startswith('django-insecure'):
        out.append(Warning('SECRET_KEY qisqa yoki taxminiy.', hint='Kamida 50 belgili tasodifiy qiymat qo‘ying: JWT va sessiyalar shunga tayanadi.', id='uzswlu.W003'))
    if '*' in settings.ALLOWED_HOSTS:
        out.append(Warning('ALLOWED_HOSTS da "*" bor.', hint='Faqat o‘z domeningizni yozing.', id='uzswlu.W004'))
    if int(settings.REST_FRAMEWORK.get('NUM_PROXIES') or 0) == 0:
        out.append(Warning('NUM_PROXIES=0: so‘rov cheklovi REMOTE_ADDR bo‘yicha ishlaydi.', hint='Nginx/Cloudflare ortida bo‘lsangiz NUM_PROXIES=1 (yoki 2) qo‘ying, aks holda hamma foydalanuvchi bitta IP ko‘rinadi.', id='uzswlu.W005'))
    local = [o for o in settings.TRUSTED_ORIGINS if '//localhost' in o or '//127.0.0.1' in o]
    if local:
        out.append(Warning('TRUSTED_ORIGINS da localhost bor: u manzillardan cookie/token bilan so‘rov yuborish mumkin.', hint='Productionda faqat admin panel va sayt domenlarini yozing: TRUSTED_ORIGINS=https://admin.sizning.uz,https://sizning.uz', id='uzswlu.W007'))
    if settings.API_DOCS_PUBLIC:
        out.append(Warning('API_DOCS_PUBLIC=true: Swagger productionda hamma uchun ochiq.', hint='API_DOCS_PUBLIC=false qiling — hujjat faqat admin panelga kirganlarga ko‘rinadi.', id='uzswlu.W006'))
    if not settings.BACKUP_ENABLED:
        out.append(Warning('BACKUP_ENABLED=0: avtomatik zaxira nusxa o‘chirilgan.', hint='Zaxirasiz server — bitta disk buzilishi hamma ma’lumotni yo‘qotadi. BACKUP_ENABLED=1 qiling.', id='uzswlu.W008'))
    elif not settings.BACKUP_COPY_TO:
        out.append(Warning('BACKUP_COPY_TO bo‘sh: zaxira faqat shu serverning o‘zida saqlanadi.', hint='Disk buzilsa zaxira ham yo‘qoladi. BACKUP_COPY_TO ga boshqa disk/ulangan tarmoq papkasini yozing yoki backups/ papkasini tashqariga (rsync/rclone) ko‘chiring.', id='uzswlu.W009'))
    return out
