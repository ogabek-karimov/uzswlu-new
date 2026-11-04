from django.contrib import admin
from django.utils.html import format_html

from .admin_base import ANY_STAFF, SUPER, BaseAdmin, RoleMixin, SingletonAdminMixin
from .models import Activity, Hit, Media, SiteSettings


@admin.register(Media)
class MediaAdmin(RoleMixin, admin.ModelAdmin):
    # Yuklash: kontent muharrirlari ham (Payload'dagi "mediaUsers"); o'chirish — faqat superadmin
    write_roles = ANY_STAFF
    read_roles = ANY_STAFF
    list_display = ('preview', 'name', 'kind', 'folder', 'size_kb', 'created_at')
    list_filter = ('kind', 'folder')
    search_fields = ('file',)
    fields = ('file', 'folder', 'alt', 'kind', 'width', 'height', 'filesize', 'original_size', 'uploaded_by')
    readonly_fields = ('kind', 'width', 'height', 'filesize', 'original_size', 'uploaded_by')
    list_per_page = 40

    def has_delete_permission(self, request, obj=None):
        return self._can(request, SUPER)

    @admin.display(description='')
    def preview(self, obj):
        if obj.kind == 'image' and obj.file:
            return format_html('<img src="{}" style="height:44px;border-radius:4px">', obj.size_url('thumb'))
        return obj.kind.upper()

    @admin.display(description='Fayl')
    def name(self, obj):
        return str(obj)

    @admin.display(description='Hajmi (KB)')
    def size_kb(self, obj):
        return round(obj.filesize / 1024) if obj.filesize else '—'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonAdminMixin, BaseAdmin):
    write_roles = SUPER
    read_roles = ANY_STAFF
    track_tags = ('settings', 'home')
    fieldsets = (
        ('Umumiy', {'fields': ('name', 'abbr', 'description')}),
        ('Aloqa', {'fields': ('phone', 'phone_ext', 'address', 'reception', 'telegram', 'instagram', 'facebook', 'youtube', 'x_url')}),
        ('Texnik yordam', {'fields': ('support_telegram', 'support_text', 'support_show_in_admin', 'support_show_on_site', 'support_pages', 'support_place')}),
        ('Bosh sahifadagi raqamlar', {'fields': ('numbers_auto', 'students', 'staff', 'faculties', 'departments')}),
    )


@admin.register(Activity)
class ActivityAdmin(RoleMixin, admin.ModelAdmin):
    write_roles = SUPER
    list_display = ('created_at', 'user_name', 'action', 'entity', 'label')
    list_filter = ('action', 'entity')
    search_fields = ('user_name', 'label')
    date_hierarchy = 'created_at'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Hit)
class HitAdmin(RoleMixin, admin.ModelAdmin):
    write_roles = SUPER
    list_display = ('ts', 'kind', 'path', 'name', 'lang', 'device', 'country')
    list_filter = ('kind', 'lang', 'device')
    date_hierarchy = 'ts'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
