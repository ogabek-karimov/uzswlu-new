from django.conf import settings
from django.http import JsonResponse
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny, BasePermission

from apps.panel.auth import PANEL_AUTH
from apps.panel.views import MediaFileCompat


class PanelUser(BasePermission):
    """Swagger productionda faqat admin panelga kirgan xodimlarga (sessiya yoki JWT)."""

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and getattr(u, 'status', '') != 'disabled')


DOCS = AllowAny if settings.API_DOCS_PUBLIC else PanelUser
SWAGGER_TEMPLATES = {'modern': 'api/swagger_modern.html', 'classic': 'api/swagger.html'}
DOCS_VIEW = {'authentication_classes': PANEL_AUTH, 'permission_classes': [DOCS]}


def healthz(request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('', RedirectView.as_view(url='/api/docs/', permanent=False)),
    path('healthz', healthz),
    # Swagger: ishlab chiqishda ochiq, productionda faqat admin panelga kirgan xodimlar uchun (API_DOCS_PUBLIC=false)
    path('api/schema/', SpectacularAPIView.as_view(**DOCS_VIEW), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema', template_name=SWAGGER_TEMPLATES.get(settings.SWAGGER_THEME, 'api/swagger_modern.html'), **DOCS_VIEW), name='swagger'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema', **DOCS_VIEW), name='redoc'),
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
