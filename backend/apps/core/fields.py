"""4 tilli maydon: { "uz": "...", "ru": "...", "en": "...", "zh": "..." } (JSON).

Sayt API shu shaklni to'g'ridan-to'g'ri ishlatadi; admin panelda esa 4 ta alohida kiritish maydoni ko'rinadi.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.db import models

LANGS = ('uz', 'ru', 'en', 'zh')
LANG_LABELS = {'uz': 'Oʻzbekcha', 'ru': 'Ruscha', 'en': 'Inglizcha', 'zh': 'Xitoycha'}


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


class I18nWidget(forms.MultiWidget):
    template_name = 'core/widgets/i18n.html'

    def __init__(self, multiline: bool = False, attrs=None):
        attrs_ = {'style': 'width:100%;max-width:720px'}
        if multiline:
            attrs_.update(rows='4', cols='60')
        cls = forms.Textarea if multiline else forms.TextInput
        widgets = [cls(attrs=dict(attrs_)) for _ in LANGS]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if isinstance(value, dict):
            return [str(value.get(lang) or '') for lang in LANGS]
        return ['' for _ in LANGS]

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        for sub, lang in zip(context['widget']['subwidgets'], LANGS):
            sub['lang'] = lang
            sub['lang_label'] = LANG_LABELS[lang]
        return context


class I18nFormField(forms.Field):
    def __init__(self, *, multiline: bool = False, required_uz: bool = False, **kwargs):
        self.required_uz = required_uz
        kwargs.setdefault('widget', I18nWidget(multiline=multiline))
        super().__init__(**kwargs)

    def prepare_value(self, value):
        return value if isinstance(value, dict) else {}

    def to_python(self, value):
        if isinstance(value, (list, tuple)):
            value = dict(zip(LANGS, value))
        if not isinstance(value, dict):
            return {}
        return {lang: str(value[lang]).strip() for lang in LANGS if value.get(lang) and str(value[lang]).strip()}

    def validate(self, value):
        super().validate(value)
        if self.required_uz and not value.get('uz'):
            raise ValidationError('Oʻzbekcha matn majburiy', code='required')


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

    def formfield(self, **kwargs):
        return models.Field.formfield(
            self,
            **{
                'form_class': I18nFormField,
                'multiline': self.multiline,
                'required_uz': self.required_uz,
                # callable default (dict) uchun yashirin "initial" maydoni kerak emas
                'show_hidden_initial': False,
                **kwargs,
            },
        )
