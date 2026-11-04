from django.contrib import admin

from apps.core.admin_base import EDITORS, FACULTY, PAGES, SUPER, BaseAdmin, BaseInline, SingletonAdminMixin

from .models import (
    AdmissionDate, AdmissionFaq, AdmissionSettings, Appeal, Campus, ContactEmail, Department, Faculty, Program,
    ProgramGroup, StaffDocument, StaffProfile,
)


@admin.register(Faculty)
class FacultyAdmin(BaseAdmin):
    write_roles = FACULTY
    track_tags = ('faculties', 'home')
    list_display = ('__str__', 'slug', 'phone', 'order')
    list_editable = ('order',)
    autocomplete_fields = ('logo', 'cover')

    def has_add_permission(self, request, obj=None):
        return self._can(request, SUPER)

    def has_delete_permission(self, request, obj=None):
        return self._can(request, SUPER)


@admin.register(Department)
class DepartmentAdmin(BaseAdmin):
    write_roles = FACULTY
    track_tags = ('faculties',)
    list_display = ('__str__', 'hemis_id', 'faculty_slug', 'room')
    list_filter = ('faculty_slug',)
    search_fields = ('hemis_id',)
    autocomplete_fields = ('image',)

    def has_delete_permission(self, request, obj=None):
        return self._can(request, SUPER)


@admin.register(StaffProfile)
class StaffProfileAdmin(BaseAdmin):
    write_roles = SUPER
    read_roles = EDITORS
    track_tags = ('staff',)
    list_display = ('__str__', 'hemis_id', 'hidden', 'updated_at')
    list_filter = ('hidden',)
    search_fields = ('hemis_id', 'name')
    autocomplete_fields = ('own_photo',)


@admin.register(StaffDocument)
class StaffDocumentAdmin(BaseAdmin):
    write_roles = SUPER
    list_display = ('__str__', 'section', 'created_at')
    list_filter = ('section',)
    search_fields = ('hemis_id',)


@admin.register(ProgramGroup)
class ProgramGroupAdmin(BaseAdmin):
    write_roles = PAGES
    track_tags = ('programs',)
    list_display = ('__str__', 'level', 'key', 'order')


@admin.register(Program)
class ProgramAdmin(BaseAdmin):
    write_roles = PAGES
    track_tags = ('programs', 'admission')
    list_display = ('code', '__str__', 'level', 'form', 'years', 'in_admission', 'order')
    list_filter = ('level', 'form', 'in_admission', 'group', 'faculty')
    list_editable = ('order',)
    search_fields = ('code',)


class AdmissionDateInline(BaseInline, admin.StackedInline):
    write_roles = PAGES
    model = AdmissionDate


class AdmissionFaqInline(BaseInline, admin.StackedInline):
    write_roles = PAGES
    model = AdmissionFaq


@admin.register(AdmissionSettings)
class AdmissionSettingsAdmin(SingletonAdminMixin, BaseAdmin):
    write_roles = PAGES
    track_tags = ('admission',)
    inlines = [AdmissionDateInline, AdmissionFaqInline]


@admin.register(Campus)
class CampusAdmin(BaseAdmin):
    write_roles = SUPER
    read_roles = PAGES
    track_tags = ('contact', 'site')
    list_display = ('__str__', 'key', 'phone', 'order')
    list_editable = ('order',)


@admin.register(ContactEmail)
class ContactEmailAdmin(BaseAdmin):
    write_roles = SUPER
    read_roles = PAGES
    track_tags = ('contact', 'site')
    list_display = ('value', 'order')
    list_editable = ('order',)


@admin.register(Appeal)
class AppealAdmin(BaseAdmin):
    write_roles = SUPER
    read_roles = EDITORS
    list_display = ('number', 'name', 'recipient_title', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('number', 'name', 'email', 'phone')
    date_hierarchy = 'created_at'
    readonly_fields = ('number', 'name', 'phone', 'email', 'recipient', 'recipient_title', 'message', 'file', 'ip', 'created_at')

    def has_add_permission(self, request, obj=None):
        return False
