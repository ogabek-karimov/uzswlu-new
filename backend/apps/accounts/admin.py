from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.core.admin_base import RoleMixin, SUPER

from .forms import UserChangeForm, UserCreationForm
from .models import StaffSession, User


@admin.register(User)
class UserAdmin(RoleMixin, DjangoUserAdmin):
    write_roles = SUPER
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ('name', 'username', 'role', 'status', 'last_login')
    list_filter = ('role', 'status')
    search_fields = ('name', 'username', 'email', 'hemis_id')
    ordering = ('name',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Shaxsiy', {'fields': ('name', 'email', 'position', 'department', 'hemis_id', 'avatar')}),
        ('Huquqlar', {'fields': ('role', 'status', 'scope', 'is_active')}),
        ('Sanalar', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('username', 'name', 'role', 'password1', 'password2')}),
    )
    raw_id_fields = ('avatar',)


@admin.register(StaffSession)
class StaffSessionAdmin(RoleMixin, admin.ModelAdmin):
    write_roles = SUPER
    list_display = ('hemis_id', 'created_at', 'expires_at', 'last_used')
    search_fields = ('hemis_id',)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
