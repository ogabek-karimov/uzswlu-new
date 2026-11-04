"""Media fayli qayerda ishlatilgan: "Qayerda ishlatilgan" ro'yxati va ishlatilayotgan faylni o'chirishdan himoya.

Media'ga bog'langan barcha maydonlar modellardan avtomatik topiladi — yangi model qo'shilsa ham ro'yxat to'liq qoladi.
"""
from apps.core.models import Media

PARENTS = ('post', 'page', 'goal', 'admission')


def _relations():
    for f in Media._meta.get_fields(include_hidden=True):
        if f.is_relation and (f.one_to_many or f.many_to_many) and f.related_model is not None:
            yield f.related_model, f.field.name, f.many_to_many


def _label(obj) -> str:
    for attr in PARENTS:
        parent = getattr(obj, attr, None)
        if parent is not None:
            obj = parent
            break
    title = getattr(obj, 'title', None)
    name = title.get('uz') if isinstance(title, dict) else None
    return f'{obj._meta.verbose_name.capitalize()}: {name or getattr(obj, "name", None) or obj}'


def media_usage(media_id: int) -> list[str]:
    out: list[str] = []
    for model, field, _ in _relations():
        for obj in model.objects.filter(**{field: media_id})[:20]:
            label = _label(obj)
            if label not in out:
                out.append(label)
    return out


def used_media_ids() -> set[int]:
    used: set[int] = set()
    for model, field, m2m in _relations():
        values = model.objects.filter(**{f'{field}__isnull': False}).values_list(field, flat=True)
        used.update(v for v in values if v)
    return used
