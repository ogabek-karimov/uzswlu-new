from django.urls import path

from . import views

urlpatterns = [
    path('status', views.StatusView.as_view()),
    path('login', views.LoginView.as_view()),
    path('callback', views.CallbackView.as_view()),
]
