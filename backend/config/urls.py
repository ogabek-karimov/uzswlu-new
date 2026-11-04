from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny, IsAdminUser

from apps.panel.views import MediaFileCompat

admin.site.site_header = 'ÖzDJTU'
admin.site.site_title = 'ÖzDJTU admin'
admin.site.index_title = 'Saytni boshqarish'


DOCS = AllowAny if settings.API_DOCS_PUBLIC else IsAdminUser


def healthz(request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('', RedirectView.as_view(url='/admin/', permanent=False)),
    path('healthz', healthz),
    path('admin/', admin.site.urls),
    # Swagger: ishlab chiqishda ochiq, productionda faqat Django admin'ga kirgan xodimlar uchun (API_DOCS_PUBLIC)
    path('api/schema/', SpectacularAPIView.as_view(permission_classes=[DOCS]), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema', permission_classes=[DOCS]), name='swagger'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema', permission_classes=[DOCS]), name='redoc'),
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
