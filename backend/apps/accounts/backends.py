"""Django admin (Jazzmin) kirishi ham Payload'dan ko'chirilgan parollarni qabul qilsin."""
from django.contrib.auth.backends import ModelBackend

from .models import User, check_any_password


class LegacyPasswordBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = User.objects.filter(username__iexact=username or '').first()
        if user and user.legacy_password and check_any_password(user, password or '') and self.user_can_authenticate(user):
            return user
        return None
