from django.contrib import admin

from apps.core.admin_base import EDITORS, PAGES, SUPER, BaseAdmin, BaseInline, SingletonAdminMixin

from .models import (
    Category, DocCategory, Document, Leader, Partner, Post, PostAttachment, PostGalleryImage, Slide,
    StateSymbol, TaughtLanguage, Video, VideoCategory, VideoPage,
)


class PostAttachmentInline(BaseInline, admin.TabularInline):
    write_roles = EDITORS
    model = PostAttachment
    autocomplete_fields = ('file',)


class PostGalleryInline(BaseInline, admin.TabularInline):
    write_roles = EDITORS
    model = PostGalleryImage
    autocomplete_fields = ('image',)


@admin.register(Category)
class CategoryAdmin(BaseAdmin):
    write_roles = SUPER
    read_roles = EDITORS
    list_display = ('key', 'name')
    search_fields = ('key',)


@admin.register(Post)
class PostAdmin(BaseAdmin):
    write_roles = EDITORS
    track_tags = ('posts', 'home')
    list_display = ('title_uz', 'type', 'status', 'hidden', 'published_at', 'sdg')
    list_filter = ('type', 'status', 'hidden', 'category', 'sdg')
    date_hierarchy = 'published_at'
    autocomplete_fields = ('cover', 'cover_ru', 'cover_en', 'cover_zh')
    inlines = [PostAttachmentInline, PostGalleryInline]
    fieldsets = (
        ('Asosiy', {'fields': ('type', 'title', 'excerpt', 'body', 'category', 'sdg', 'tags')}),
        ('Rasm', {'fields': ('cover', 'cover_ru', 'cover_en', 'cover_zh')}),
        ('Nashr', {'fields': ('status', 'published_at', 'hidden', 'slug', 'author')}),
        ('Tadbir uchun', {'fields': ('starts_at', 'ends_at', 'location')}),
    )

    @admin.display(description='Sarlavha', ordering='id')
    def title_uz(self, obj):
        return obj.title.get('uz', '—')

    def save_model(self, request, obj, form, change):
        if not change and not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Slide)
class SlideAdmin(BaseAdmin):
    write_roles = SUPER
    read_roles = EDITORS
    track_tags = ('home',)
    list_display = ('name', 'order', 'starts_at', 'ends_at')
    list_editable = ('order',)
    autocomplete_fields = ('image',)


@admin.register(Leader)
class LeaderAdmin(BaseAdmin):
    write_roles = SUPER
    read_roles = EDITORS
    track_tags = ('leadership', 'contact')
    list_display = ('name', 'kind', 'order', 'reception')
    list_editable = ('order',)
    autocomplete_fields = ('photo',)


@admin.register(DocCategory)
class DocCategoryAdmin(BaseAdmin):
    write_roles = PAGES
    track_tags = ('documents',)
    list_display = ('__str__', 'order')
    list_editable = ('order',)


@admin.register(Document)
class DocumentAdmin(BaseAdmin):
    write_roles = PAGES
    track_tags = ('documents',)
    list_display = ('__str__', 'category', 'display', 'downloads', 'order')
    list_filter = ('category', 'display')
    list_editable = ('order',)
    autocomplete_fields = ('file_uz', 'file_ru', 'file_en', 'file_zh')
    readonly_fields = ('downloads',)


@admin.register(VideoCategory)
class VideoCategoryAdmin(BaseAdmin):
    write_roles = PAGES
    track_tags = ('videos',)
    list_display = ('key', '__str__', 'order')


@admin.register(Video)
class VideoAdmin(BaseAdmin):
    write_roles = PAGES
    track_tags = ('videos',)
    list_display = ('__str__', 'category', 'teacher', 'order')
    list_filter = ('category',)
    list_editable = ('order',)


@admin.register(VideoPage)
class VideoPageAdmin(SingletonAdminMixin, BaseAdmin):
    write_roles = PAGES
    track_tags = ('videos',)


@admin.register(StateSymbol)
class StateSymbolAdmin(BaseAdmin):
    write_roles = SUPER
    read_roles = EDITORS
    track_tags = ('home', 'symbols')
    list_display = ('key', 'title')
    autocomplete_fields = ('image', 'audio')


@admin.register(Partner)
class PartnerAdmin(BaseAdmin):
    write_roles = SUPER
    read_roles = EDITORS
    track_tags = ('home',)
    list_display = ('__str__', 'url', 'order')
    list_editable = ('order',)
    autocomplete_fields = ('logo',)


@admin.register(TaughtLanguage)
class TaughtLanguageAdmin(BaseAdmin):
    write_roles = SUPER
    read_roles = EDITORS
    track_tags = ('home',)
    list_display = ('code', 'native', 'order')
    list_editable = ('order',)
