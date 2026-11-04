from django.contrib import admin

from .models import HemisSnapshot


@admin.register(HemisSnapshot)
class HemisSnapshotAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'synced_at', 'error')
    readonly_fields = ('synced_at', 'error', 'data')

    def has_add_permission(self, request):
        return False
