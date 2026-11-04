from django.contrib import admin

from .models import LoginEvent, Version


class ReadOnly(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(LoginEvent)
class LoginEventAdmin(ReadOnly):
    list_display = ('created_at', 'username', 'result', 'method', 'ip', 'browser', 'os', 'device')
    list_filter = ('result', 'method', 'device')
    search_fields = ('username', 'ip')
    date_hierarchy = 'created_at'


@admin.register(Version)
class VersionAdmin(ReadOnly):
    list_display = ('entity', 'entity_id', 'user', 'created_at')
    list_filter = ('entity',)
