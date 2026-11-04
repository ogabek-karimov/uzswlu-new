from django.contrib import admin

from apps.core.admin_base import PAGES, SDG, SUPER, BaseAdmin, BaseInline, SingletonAdminMixin

from .models import (
    Page, PageAttachment, PageFact, PageTimeline, SdgCategory, SdgGoal, SdgGoalReport, SdgOverviewReport, SdgPage, SdgSection,
)


class PageFactInline(BaseInline, admin.TabularInline):
    write_roles = PAGES
    model = PageFact


class PageTimelineInline(BaseInline, admin.StackedInline):
    write_roles = PAGES
    model = PageTimeline


class PageAttachmentInline(BaseInline, admin.StackedInline):
    write_roles = PAGES
    model = PageAttachment
    autocomplete_fields = ('file',)


@admin.register(Page)
class PageAdmin(BaseAdmin):
    write_roles = PAGES
    track_tags = ('menu', 'pages')
    list_display = ('__str__', 'template', 'parent', 'site_url', 'in_menu', 'published', 'order')
    list_filter = ('template', 'in_menu', 'published', 'parent')
    list_editable = ('order',)
    search_fields = ('slug', 'url')
    autocomplete_fields = ('file',)
    inlines = [PageFactInline, PageTimelineInline, PageAttachmentInline]
    fieldsets = (
        ('Joylashuvi', {'fields': ('title', 'template', 'parent', 'order', 'in_menu', 'published', 'highlight', 'sdg')}),
        ('Manzil', {'fields': ('slug', 'url', 'file', 'group_key', 'overview', 'description')}),
        ('Matnli sahifa mazmuni', {'fields': ('lead', 'body')}),
    )

    @admin.display(description='Sayt manzili')
    def site_url(self, obj):
        return obj.site_url


class SdgSectionInline(BaseInline, admin.StackedInline):
    write_roles = SDG
    model = SdgSection
    autocomplete_fields = ('images',)


class SdgGoalReportInline(BaseInline, admin.StackedInline):
    write_roles = SDG
    model = SdgGoalReport
    autocomplete_fields = ('file',)


@admin.register(SdgGoal)
class SdgGoalAdmin(BaseAdmin):
    # 17 maqsad o'zgarmaydi (qo'shilmaydi, o'chirilmaydi); mazmunini superadmin va BRM menejeri tahrirlaydi
    write_roles = SDG
    track_tags = ('sdg',)
    list_display = ('n', '__str__', 'impact_rank', 'impact_score')
    inlines = [SdgSectionInline, SdgGoalReportInline]

    def has_add_permission(self, request, obj=None):
        return self._can(request, SUPER)

    def has_delete_permission(self, request, obj=None):
        return self._can(request, SUPER)


class SdgCategoryInline(BaseInline, admin.StackedInline):
    write_roles = SDG
    model = SdgCategory


class SdgOverviewReportInline(BaseInline, admin.StackedInline):
    write_roles = SDG
    model = SdgOverviewReport
    autocomplete_fields = ('file',)


@admin.register(SdgPage)
class SdgPageAdmin(SingletonAdminMixin, BaseAdmin):
    write_roles = SDG
    track_tags = ('sdg',)
    inlines = [SdgCategoryInline, SdgOverviewReportInline]
