"""Vue admin panel API'si: /api/cms/* (Payload REST bilan bir xil manzillar va javoblar)."""
from django.urls import path

from . import auth, dashboard, twofactor
from . import views as v

urlpatterns = [
    path('private/<path:name>', v.PrivateFileView.as_view()),  # yopiq fayllar — kolleksiya yo'llaridan OLDIN
    path('users/login', auth.LoginView.as_view()),
    path('users/login/2fa', twofactor.LoginTwoFactorView.as_view()),
    path('users/2fa/setup', twofactor.SetupView.as_view()),
    path('users/2fa/enable', twofactor.EnableView.as_view()),
    path('users/2fa/disable', twofactor.DisableView.as_view()),
    path('users/2fa/recovery', twofactor.RecoveryView.as_view()),
    path('users/2fa/reset', twofactor.ResetView.as_view()),
    path('users/logout', auth.LogoutView.as_view()),
    path('users/me', auth.MeView.as_view()),
    path('users/refresh-token', auth.RefreshTokenView.as_view()),
    path('users/unlock', auth.UnlockView.as_view()),

    path('panel/overview', dashboard.OverviewView.as_view()),
    path('panel/stats', dashboard.StatsView.as_view()),
    path('panel/media-stats', dashboard.MediaStatsView.as_view()),
    path('panel/media-usage/<int:pk>', dashboard.MediaUsageView.as_view()),
    path('panel/media-used', dashboard.MediaUsedView.as_view()),
    path('panel/youtube', dashboard.YoutubeView.as_view()),
    path('panel/hemis', dashboard.HemisView.as_view()),
    path('panel/sdg-counts', dashboard.SdgCountsView.as_view()),

    path('globals/<slug:slug>', v.GlobalView.as_view()),
    path('globals/<slug:slug>/versions', v.GlobalVersionsView.as_view()),
    path('globals/<slug:slug>/versions/<int:vid>', v.GlobalVersionsView.as_view()),

    path('<slug:slug>/count', v.CollectionCountView.as_view()),
    path('<slug:slug>/versions', v.VersionsView.as_view()),
    path('<slug:slug>/versions/<int:vid>', v.VersionsView.as_view()),
    path('<slug:slug>/<int:pk>', v.DocView.as_view()),
    path('<slug:slug>', v.CollectionView.as_view()),
]
