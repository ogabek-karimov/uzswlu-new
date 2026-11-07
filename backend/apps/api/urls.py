"""API manzillari. Asosiy shartnoma — frontend/docs/openapi.yaml (`/api/home`, `/api/posts` …).

`/api/site/*` — Payload CMS'dagi eski manzillarning nusxasi: frontend `NUXT_CMS_BASE=<backend>/api/site` bilan ishlaganda ham
to'g'ri javob olsin (token talab qilinmaydi, `/hit` shu yerda ham bor).
"""
from django.urls import path

from . import views as v
from . import views_staff as s

urlpatterns = [
    path('home', v.HomeView.as_view()),
    path('site', v.SiteView.as_view()),
    path('staff', s.StaffListView.as_view()),
    path('staff/<str:pk>', s.StaffDetailView.as_view()),
    path('me', s.MeView.as_view()),
    path('me/avatar', s.MeAvatarView.as_view()),
    path('me/documents/<str:section>', s.MeDocumentsView.as_view()),
    path('me/documents/<str:section>/<str:pk>', s.MeDocumentDetailView.as_view()),
    path('pages/<slug:slug>', v.PageView.as_view()),
    path('posts', v.PostListView.as_view()),
    path('posts/<str:type>/<str:slug>', v.PostDetailView.as_view()),
    path('events', v.EventsView.as_view()),
    path('leadership', v.LeadershipView.as_view()),
    path('documents', v.DocumentsView.as_view()),
    path('documents/<int:pk>/file', v.DocumentFileView.as_view()),
    path('programs', v.ProgramsView.as_view()),
    path('faculties', v.FacultyListView.as_view()),
    path('faculties/<slug:slug>', v.FacultyDetailView.as_view()),
    path('admission', v.AdmissionView.as_view()),
    path('sdg', v.SdgOverviewView.as_view()),
    path('sdg/<int:n>', v.SdgGoalView.as_view()),
    path('videos', v.VideosView.as_view()),
    path('contact', v.ContactView.as_view()),
    path('appeals', v.AppealView.as_view()),
    path('search', v.SearchView.as_view()),
    path('hit', v.HitView.as_view()),
]


def _open(view):
    """Payload'dagi /site/* ochiq edi — token talab qilinmaydi."""
    return view.as_view(permission_classes=[])


urlpatterns += [
    path('site/latest', _open(v.LatestView)),
    path('site/slides', _open(v.SlidesView)),
    path('site/index', _open(v.PostIndexView)),
    path('site/settings', _open(v.SettingsView)),
    path('site/symbols', _open(v.SymbolsView)),
    path('site/menu', _open(v.MenuView)),
    path('site/sdg-goals', _open(v.SdgGoalsView)),
    # Yashirilgan xodimlar ro'yxati ochiq emas: API_TOKEN belgilangan bo'lsa token talab qilinadi (asosiy /api/staff ro'yxati yashirinlarni o'zi chiqarmaydi)
    path('site/staff-hidden', s.StaffHiddenView.as_view()),
    path('site/staff/<str:pk>', _open(s.StaffOverlayView)),
    path('site/posts', _open(v.PostListView)),
    path('site/posts/<str:type>/<str:slug>', _open(v.PostDetailView)),
    path('site/events', _open(v.EventsView)),
    path('site/leadership', _open(v.LeadershipView)),
    path('site/documents', _open(v.DocumentsView)),
    path('site/documents/<int:pk>/file', v.DocumentFileView.as_view()),
    path('site/videos', _open(v.VideosView)),
    path('site/pages/<slug:slug>', _open(v.PageView)),
    path('site/faculties', _open(v.FacultyListView)),
    path('site/faculties/<slug:slug>', _open(v.FacultyDetailView)),
    path('site/sdg/<int:n>', _open(v.SdgGoalView)),
    path('site/hit', v.HitView.as_view()),
]
