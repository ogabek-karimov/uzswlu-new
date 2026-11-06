"""4 tilli maydon: { "uz": "...", "ru": "...", "en": "...", "zh": "..." } (JSON).

Sayt API shu shaklni to'g'ridan-to'g'ri ishlatadi; admin panel (Vue) esa 4 ta alohida kiritish maydoni ko'rsatadi.
"""
from django.db import models

LANGS = ('uz', 'ru', 'en', 'zh')


def is_lang(value) -> bool:
    return isinstance(value, str) and value in LANGS


def pick(value, lang: str):
    """Tanlangan tildagi qiymat; bo'sh bo'lsa None."""
    if not isinstance(value, dict):
        return None
    v = value.get(lang)
    return v if isinstance(v, str) and v.strip() else None


def tr(value, lang: str) -> str:
    """Tanlangan til, bo'lmasa o'zbekcha, bo'lmasa bo'sh satr."""
    return pick(value, lang) or pick(value, 'uz') or ''


class I18nField(models.JSONField):
    """{uz, ru, en, zh} — faqat o'zbekcha majburiy bo'lishi mumkin (required_uz)."""

    description = '4 tilli matn'

    def __init__(self, *args, multiline: bool = False, required_uz: bool = False, **kwargs):
        self.multiline = multiline
        self.required_uz = required_uz
        kwargs.setdefault('default', dict)
        kwargs.setdefault('blank', True)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.multiline:
            kwargs['multiline'] = True
        if self.required_uz:
            kwargs['required_uz'] = True
        return name, path, args, kwargs
