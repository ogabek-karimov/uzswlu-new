"""Admin panel: rollar bo'yicha ruxsat (Payload'dagi qoidalar), faollik jurnali va bitta yozuvli sozlamalar."""
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse

from .activity import log_activity, purge_site_cache, short

SUPER = ()                                   # faqat superadmin
EDITORS = ('editor',)                        # kontent muharriri
PAGES = ('pages',)                           # sahifalar muharriri
FACULTY = ('faculty',)                       # fakultet admini
SDG = ('sdg',)                               # BRM menejeri
ANY_STAFF = ('editor', 'pages', 'faculty', 'sdg')


class RoleMixin:
    """write_roles — o'zgartira oladigan rollar (superadmin doim ruxsatli); read_roles — ko'ra oladiganlar."""

    write_roles: tuple = SUPER
    read_roles: tuple | None = None

    def _can(self, request, roles) -> bool:
        u = request.user
        return bool(u.is_active and u.is_staff and (u.is_superuser or getattr(u, 'role', None) in roles))

    def _read(self):
        return self.write_roles if self.read_roles is None else tuple(self.read_roles) + tuple(self.write_roles)

    def has_module_permission(self, request):
        return self._can(request, self._read())

    def has_view_permission(self, request, obj=None):
        return self._can(request, self._read())

    def has_add_permission(self, request, obj=None):
        return self._can(request, self.write_roles)

    def has_change_permission(self, request, obj=None):
        return self._can(request, self.write_roles)

    def has_delete_permission(self, request, obj=None):
        return self._can(request, self.write_roles)


class TrackedMixin:
    """Saqlash/o'chirish faollik jurnaliga yoziladi, sayt keshi yangilanadi."""

    track_tags: tuple = ()

    def _entity(self):
        return self.model._meta.label_lower

    def _label(self, obj) -> str:
        return str(obj)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        changes = {}
        if change:
            for name in form.changed_data:
                changes[name] = {'before': short(form.initial.get(name)), 'after': short(form.cleaned_data.get(name))}
        if not change or changes:
            log_activity(request, action='edit' if change else 'create', entity=self._entity(), entity_id=obj.pk, label=self._label(obj), changes=changes)
        purge_site_cache(self.track_tags)

    def delete_model(self, request, obj):
        label, pk = self._label(obj), obj.pk
        super().delete_model(request, obj)
        log_activity(request, action='delete', entity=self._entity(), entity_id=pk, label=label)
        purge_site_cache(self.track_tags)

    def delete_queryset(self, request, queryset):
        items = [(o.pk, self._label(o)) for o in queryset]
        super().delete_queryset(request, queryset)
        for pk, label in items:
            log_activity(request, action='delete', entity=self._entity(), entity_id=pk, label=label)
        purge_site_cache(self.track_tags)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        purge_site_cache(self.track_tags)


class SingletonAdminMixin:
    """Bitta yozuvli sozlama: ro'yxat o'rniga to'g'ridan-to'g'ri tahrirlash sahifasi."""

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = self.model.load()
        opts = self.model._meta
        return redirect(reverse(f'admin:{opts.app_label}_{opts.model_name}_change', args=[obj.pk]))


class BaseAdmin(TrackedMixin, RoleMixin, admin.ModelAdmin):
    save_on_top = True


class BaseInline(RoleMixin):
    extra = 0
