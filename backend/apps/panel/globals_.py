"""Vue admin panel global sozlamalari (bitta yozuvli): sayt sozlamalari, video sahifasi, ramzlar, BRM sahifasi."""
from django.core.exceptions import ValidationError

from apps.content.models import StateSymbol, VideoPage
from apps.core.models import SiteSettings
from apps.pages.models import SdgPage

from .collections import ALL, PAGES, SDG, SUPER, dt, flag, i18n_in, i18n_out, media_out, media_ref, num, parse_dt, text


class Global:
    slug = ''
    entity = ''
    label = ''
    tags: tuple = ()
    versions = 0
    access = {'read': ALL, 'update': SUPER}

    def can(self, user, action: str) -> bool:
        if action == 'read' and self.access.get('read') is None:
            return True
        return bool(user and user.is_authenticated and user.status != 'disabled' and user.role in self.access.get(action, ()))

    def load(self):
        raise NotImplementedError

    def out(self, obj, depth: int) -> dict:
        raise NotImplementedError

    def write(self, obj, data: dict, request):
        raise NotImplementedError


class Settings(Global):
    slug = 'settings'
    entity = 'settings'
    label = 'Sayt sozlamalari'
    tags = ('site', 'home', 'contact')
    versions = 200
    # Admin panel menyusidagi "Texnik yordam" tugmasi hamma uchun kerak — o'qish ochiq
    access = {'read': None, 'update': SUPER}

    def load(self):
        return SiteSettings.load()

    def out(self, s, depth):
        return {
            'id': 1, 'globalType': 'settings',
            'site': {'name': i18n_out(s.name), 'abbr': i18n_out(s.abbr), 'description': i18n_out(s.description)},
            'contact': {
                'phone': s.phone or None, 'email': s.email or None, 'address': i18n_out(s.address), 'telegram': s.telegram or None,
                'instagram': s.instagram or None, 'facebook': s.facebook or None, 'youtube': s.youtube or None,
            },
            'support': {
                'telegram': s.support_telegram or None, 'text': i18n_out(s.support_text), 'showInAdmin': s.support_show_in_admin,
                'showOnSite': s.support_show_on_site, 'pages': [p.strip() for p in (s.support_pages or '').split(',') if p.strip()],
                'place': s.support_place,
            },
            'numbers': {'auto': s.numbers_auto, 'students': s.students, 'staff': s.staff, 'faculties': s.faculties, 'departments': s.departments},
            'updatedAt': dt(s.updated_at), 'createdAt': dt(s.updated_at),
        }

    def write(self, s, data, request):
        site = data.get('site')
        if isinstance(site, dict):
            for key in ('name', 'abbr', 'description'):
                if key in site:
                    setattr(s, key, i18n_in(site[key]))
        contact = data.get('contact')
        if isinstance(contact, dict):
            for key in ('phone', 'email', 'telegram', 'instagram', 'facebook', 'youtube'):
                if key in contact:
                    setattr(s, key, text(contact[key]))
            if 'address' in contact:
                s.address = i18n_in(contact['address'])
        support = data.get('support')
        if isinstance(support, dict):
            if 'telegram' in support:
                s.support_telegram = text(support['telegram'])
            if 'text' in support:
                s.support_text = i18n_in(support['text'])
            if 'showInAdmin' in support:
                s.support_show_in_admin = flag(support['showInAdmin'])
            if 'showOnSite' in support:
                s.support_show_on_site = flag(support['showOnSite'])
            if 'pages' in support:
                s.support_pages = ','.join(str(p).strip() for p in support['pages'] or [] if str(p).strip())
            if support.get('place') in dict(SiteSettings._meta.get_field('support_place').choices):
                s.support_place = support['place']
        numbers = data.get('numbers')
        if isinstance(numbers, dict):
            if 'auto' in numbers:
                s.numbers_auto = flag(numbers['auto'])
            for key in ('students', 'staff', 'faculties', 'departments'):
                if key in numbers:
                    setattr(s, key, num(numbers[key], None))
        if not s.name.get('uz'):
            raise ValidationError('Universitet nomi (o‘zbekcha) majburiy')


class VideoPageGlobal(Global):
    slug = 'video-page'
    entity = 'video-page'
    label = 'Video sahifasi'
    tags = ('videos',)
    access = {'read': ALL, 'update': PAGES}

    def load(self):
        return VideoPage.load()

    def out(self, v, depth):
        return {'id': 1, 'globalType': 'video-page', 'live': v.live, 'liveUrl': v.live_url or None, 'nextTitle': i18n_out(v.next_title),
                'nextAt': dt(v.next_at), 'channelUrl': v.channel_url or None}

    def write(self, v, data, request):
        if 'live' in data:
            v.live = flag(data['live'])
        if 'liveUrl' in data:
            v.live_url = text(data['liveUrl'])
        if 'nextTitle' in data:
            v.next_title = i18n_in(data['nextTitle'])
        if 'nextAt' in data:
            v.next_at = parse_dt(data['nextAt'])
        if 'channelUrl' in data and text(data['channelUrl']):
            v.channel_url = text(data['channelUrl'])


class SymbolsGlobal(Global):
    """Uchta StateSymbol yozuvi (emblem, flag, anthem) — Payload'da bitta global edi."""

    slug = 'symbols'
    entity = 'symbols'
    label = 'Davlat ramzlari'
    tags = ('home', 'symbols', 'site')

    def load(self):
        rows = {s.key: s for s in StateSymbol.objects.select_related('image', 'audio')}
        for key, _ in StateSymbol.KEYS:
            if key not in rows:
                rows[key] = StateSymbol.objects.create(key=key, title={'uz': dict(StateSymbol.KEYS)[key]})
        return rows

    def out(self, rows, depth):
        doc = {'id': 1, 'globalType': 'symbols'}
        for key, s in rows.items():
            item = {
                'image': media_out(s.image, depth) if s.image_id else None, 'title': i18n_out(s.title),
                'description': i18n_out(s.description), 'link': s.link or None, 'source': s.source or None,
            }
            if key == 'anthem':
                item['audio'] = media_out(s.audio, depth) if s.audio_id else None
            doc[key] = item
        return doc

    def write(self, rows, data, request):
        for key, s in rows.items():
            item = data.get(key)
            if not isinstance(item, dict):
                continue
            if 'image' in item:
                s.image = media_ref(item['image'])
            if key == 'anthem' and 'audio' in item:
                s.audio = media_ref(item['audio'])
            if 'title' in item:
                s.title = i18n_in(item['title']) or s.title
            if 'description' in item:
                s.description = i18n_in(item['description'])
            if 'link' in item:
                s.link = text(item['link'])
            if 'source' in item:
                s.source = text(item['source'])
            s._dirty = True


class SdgPageGlobal(Global):
    slug = 'sdg-page'
    entity = 'sdg-page'
    label = 'BRM sahifasi'
    tags = ('sdg',)
    access = {'read': ALL, 'update': SDG}

    def load(self):
        return SdgPage.load()

    def out(self, p, depth):
        return {'id': 1, 'globalType': 'sdg-page', 'impactYear': p.impact_year}

    def write(self, p, data, request):
        if 'impactYear' in data and data['impactYear'] not in (None, ''):
            p.impact_year = num(data['impactYear'])


GLOBALS: dict[str, Global] = {g.slug: g for g in (Settings(), VideoPageGlobal(), SymbolsGlobal(), SdgPageGlobal())}


def save_global(g: Global, obj):
    if isinstance(obj, dict):
        for s in obj.values():
            s.save()
    else:
        obj.save()
