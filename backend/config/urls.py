from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.views.static import serve

admin.site.site_header = 'ÖzDJTU'
admin.site.site_title = 'ÖzDJTU admin'
admin.site.index_title = 'Saytni boshqarish'


def healthz(request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('', RedirectView.as_view(url='/admin/', permanent=False)),
    path('healthz', healthz),
    path('admin/', admin.site.urls),
    path('api/', include('apps.api.urls')),
]

# Yuklangan fayllar: ishlab chiqishda Django o'zi beradi; productionda Nginx `/media/` ni to'g'ridan-to'g'ri beradi (SERVE_MEDIA=false)
if settings.SERVE_MEDIA:
    urlpatterns += [re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})]
