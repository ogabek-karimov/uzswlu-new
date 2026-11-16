import threading
import time

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.swagger import ALL_ROLES, filter_by_role
from apps.core.docsgen import HANDBOOK
from apps.core.throttles import ScopedThrottle
from apps.panel.auth import PANEL_AUTH
from apps.panel.views import MediaFileCompat


class PanelUser(BasePermission):
    """Swagger productionda faqat admin panelga kirgan xodimlarga (sessiya yoki JWT)."""

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and getattr(u, 'status', '') != 'disabled')


DOCS = AllowAny if settings.API_DOCS_PUBLIC else PanelUser
SWAGGER_TEMPLATES = {'modern': 'api/swagger_modern.html', 'classic': 'api/swagger.html'}


class _Limited:
    """Sxema yaratish og'ir amal: hujjat sahifalari so'rov cheklovi bilan."""
    throttle_classes = [ScopedThrottle]
    throttle_scope = 'docs'


_schema_lock = threading.Lock()
_schema_cache: dict = {'at': 0.0, 'data': None}
SCHEMA_TTL = 300  # soniya; sxema kodga bog'liq (viewerga emas), kod o'zgarsa — jarayon qayta ishga tushadi


class SchemaView(_Limited, SpectacularAPIView):
    """Sxema generatsiyasi og'ir va parallel chaqiruvda xavfsiz emas: ketma-ket bajariladi, productionda xotirada keshlanadi."""

    def get(self, request, *args, **kwargs):
        with _schema_lock:
            fresh = _schema_cache['data'] is not None and time.monotonic() - _schema_cache['at'] < SCHEMA_TTL
            if settings.DEBUG or not fresh or request.query_params.get('lang'):
                response = super().get(request, *args, **kwargs)
                if not settings.DEBUG and not request.query_params.get('lang') and isinstance(response.data, dict):
                    _schema_cache.update(at=time.monotonic(), data=response.data)
            else:
                response = Response(_schema_cache['data'])
        role = request.query_params.get('role')  # ?role=editor — faqat shu rolga ruxsat etilgan amallar
        if role in ALL_ROLES and isinstance(response.data, dict):
            response.data = filter_by_role(response.data, role)
        return response


class HandbookView(_Limited, APIView):
    """Loyiha qo'llanmasi (docs/index.html nusxasi): Swagger sahifasida «Loyiha qo'llanmasi» bo'limida iframe ichida ochiladi.
    Ruxsat Swagger bilan bir xil (API_DOCS_PUBLIC). Faqat shu sahifa o'z saytimiz ichida ramkaga olinadi (SAMEORIGIN)."""

    def get(self, request):
        try:
            html = HANDBOOK.read_text(encoding='utf-8')
        except OSError:
            return HttpResponse("Qo'llanma topilmadi: `cd backend && python manage.py build_docs`", status=404, content_type='text/plain; charset=utf-8')
        response = HttpResponse(html, content_type='text/html; charset=utf-8')
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['Content-Security-Policy'] = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'self' data:; font-src data:; frame-ancestors 'self'"
        response['Cache-Control'] = 'private, no-store'
        return response


class SwaggerView(_Limited, SpectacularSwaggerView):
    pass


class RedocView(_Limited, SpectacularRedocView):
    pass


DOCS_VIEW = {'authentication_classes': PANEL_AUTH, 'permission_classes': [DOCS]}


def healthz(request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('', RedirectView.as_view(url='/api/docs/', permanent=False)),
    path('healthz', healthz),
    # Swagger: ishlab chiqishda ochiq, productionda faqat admin panelga kirgan xodimlar uchun (API_DOCS_PUBLIC=false)
    path('api/schema/', SchemaView.as_view(**DOCS_VIEW), name='schema'),
    path('api/docs/', SwaggerView.as_view(url_name='schema', template_name=SWAGGER_TEMPLATES.get(settings.SWAGGER_THEME, 'api/swagger_modern.html'), **DOCS_VIEW), name='swagger'),
    path('api/docs/handbook/', HandbookView.as_view(**DOCS_VIEW), name='handbook'),
    path('api/redoc/', RedocView.as_view(url_name='schema', **DOCS_VIEW), name='redoc'),
    # Vue admin panel API'si (Payload bilan bir xil shakl)
    path('api/cms/', include('apps.panel.urls')),
    path('api/auth/hemis/', include('apps.hemis.urls')),
    # Payload'dagi fayl manzillari (eski havolalar ishlayversin)
    path('api/media/file/<path:name>', MediaFileCompat.as_view()),
    path('api/', include('apps.api.urls')),
]

# Yuklangan fayllar: ishlab chiqishda Django o'zi beradi; productionda Nginx `/media/` ni to'g'ridan-to'g'ri beradi (SERVE_MEDIA=false)
if settings.SERVE_MEDIA:
    urlpatterns += [re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})]
