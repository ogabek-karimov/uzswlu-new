"""Payload CMS (oldingi backend) bazasidagi ma'lumotlarni shu Django bazasiga ko'chirish.

    python manage.py import_payload --db postgres://uzswlu:***@host:5432/uzswlu \
        --media-url http://host:3001/api/media/file/  [--replace]

Payload bazasi faqat o'qiladi (o'zgarmaydi). Ko'chiriladi: fayllar (rasm, PDF, audio), foydalanuvchilar (parollari bilan),
postlar (galereya, PDF, teglar, savat), karusel, rektorat, hujjatlar, video, ramzlar, fakultetlar, kafedralar, xodim
profillari, BRM, sahifalar daraxti, sayt sozlamalari, faollik jurnali va kirish tarixi.
--replace — shu backend'dagi namunaviy kontentni avval o'chiradi (foydalanuvchilar saqlanadi).
"""
import os
import re
import urllib.parse
import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import User
from apps.content.models import (
    Category, DocCategory, Document, Leader, Post, PostAttachment, PostGalleryImage, Slide, StateSymbol, Video,
    VideoCategory, VideoPage,
)
from apps.core.models import Activity, Media, SiteSettings
from apps.pages.models import Page, PageAttachment, PageFact, PageTimeline, SdgGoal, SdgGoalReport, SdgPage, SdgSection
from apps.panel.models import LoginEvent
from apps.structure.models import Department, Faculty, StaffProfile

LANGS = ('uz', 'ru', 'en', 'zh')


def i18n(row: dict, prefix: str) -> dict:
    return {lang: row[f'{prefix}_{lang}'].strip() for lang in LANGS if (row.get(f'{prefix}_{lang}') or '').strip()}


class Command(BaseCommand):
    help = 'Payload CMS bazasidagi ma’lumot va fayllarni shu backend’ga ko‘chiradi'

    def add_arguments(self, parser):
        parser.add_argument('--db', default=os.environ.get('PAYLOAD_DATABASE_URL'), help='Payload bazasi (postgres://…)')
        parser.add_argument('--media-dir', default=os.environ.get('PAYLOAD_MEDIA_DIR'), help='Payload media papkasi')
        parser.add_argument('--media-url', default=os.environ.get('PAYLOAD_MEDIA_URL'), help='…/api/media/file/ (papka bo‘lmasa)')
        parser.add_argument('--replace', action='store_true', help='Avval shu backend’dagi kontentni o‘chirish')

    # ── yordamchilar ──
    def rows(self, sql: str, *params) -> list[dict]:
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [c.name for c in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]

    def children(self, table: str) -> dict:
        out: dict = {}
        for r in self.rows(f'SELECT * FROM {table} ORDER BY _parent_id, _order'):
            out.setdefault(r['_parent_id'], []).append(r)
        return out

    def texts(self, table: str) -> dict:
        """hasMany matn (teglar, sahifalar): {(parent_id, path): [..]}"""
        out: dict = {}
        for r in self.rows(f'SELECT parent_id, path, text FROM {table} ORDER BY parent_id, "order"'):
            out.setdefault((r['parent_id'], r['path']), []).append(r['text'])
        return out

    def m(self, payload_id):
        return self.media.get(payload_id) if payload_id else None

    def fetch_file(self, filename: str) -> bytes | None:
        if self.media_dir:
            path = os.path.join(self.media_dir, filename)
            if os.path.isfile(path):
                with open(path, 'rb') as fh:
                    return fh.read()
        if self.media_url:
            url = self.media_url.rstrip('/') + '/' + urllib.parse.quote(filename)
            try:
                with urllib.request.urlopen(url, timeout=60) as res:  # noqa: S310 — manzilni admin beradi
                    return res.read()
            except Exception:  # noqa: BLE001
                return None
        return None

    def fix_html(self, html: str | None) -> str:
        """Matn ichidagi Payload fayl manzillari → yangi manzillar."""
        if not html:
            return html or ''
        def repl(match):
            new = self.media_urls.get(urllib.parse.unquote(match.group(2)))
            return new or match.group(0)
        return re.sub(r'(https?://[^"\'\s>]*)?/api/media/file/([^"\'\s>?#]+)', repl, html)

    def fix_i18n_html(self, value: dict) -> dict:
        return {k: self.fix_html(v) for k, v in value.items()}

    def stamp(self, model, pk, **dates):
        dates = {k: v for k, v in dates.items() if v}
        if dates:
            model.objects.filter(pk=pk).update(**dates)

    # ── asosiy ──
    def handle(self, *args, **o):
        if not o['db']:
            raise CommandError('Payload bazasi ko‘rsatilmagan: --db yoki PAYLOAD_DATABASE_URL')
        import psycopg
        self.conn = psycopg.connect(o['db'])
        self.conn.read_only = True
        self.media_dir, self.media_url = o['media_dir'], o['media_url']
        self.media, self.media_urls, self.users = {}, {}, {}
        with transaction.atomic():
            if o['replace']:
                self.clear()
            self.import_media()
            self.import_users()
            cats = self.import_posts()
            self.import_simple()
            self.import_structure()
            self.import_sdg()
            self.import_pages()
            self.import_globals()
            self.import_history()
        self.conn.close()
        self.stdout.write(self.style.SUCCESS(
            f'Ko‘chirildi: {len(self.media)} fayl, {len(self.users)} foydalanuvchi, {Post.objects.count()} post, '
            f'{Page.objects.count()} sahifa, {cats} kategoriya'))

    def clear(self):
        for model in (PostAttachment, PostGalleryImage, Post, Category, Slide, Leader, Document, DocCategory, Video, VideoCategory,
                      PageAttachment, PageFact, PageTimeline, SdgSection, SdgGoalReport, StaffProfile, Department):
            model.objects.all().delete()
        Page.objects.filter(parent__isnull=False).delete()
        while Page.objects.exists():
            Page.objects.filter(children__isnull=True).delete()
        StateSymbol.objects.update(image=None, audio=None)
        Faculty.objects.update(logo=None, cover=None)
        # Faqat endi hech qayerda ishlatilmayotgan fayllar o'chiriladi (masalan, hamkorlar logolari qoladi)
        from apps.panel.usage import used_media_ids
        used = used_media_ids()
        for media in Media.objects.exclude(pk__in=used):
            for path in (media.sizes or {}).values():
                media.file.storage.delete(path)
            media.file.delete(save=False)
            media.delete()

    def import_media(self):
        missing = 0
        for r in self.rows('SELECT * FROM media ORDER BY id'):
            data = self.fetch_file(r['filename'])
            if data is None:
                missing += 1
                continue
            obj = Media(folder=r['folder'] or 'posts', alt=i18n(r, 'alt'))
            obj.file = ContentFile(data, name=r['filename'])
            obj.save()
            self.stamp(Media, obj.pk, created_at=r['created_at'])
            self.media[r['id']] = obj
            self.media_urls[r['filename']] = obj.url
            for size in ('thumb', 'card', 'hero'):
                if r.get(f'sizes_{size}_filename'):
                    self.media_urls[r[f'sizes_{size}_filename']] = obj.size_url(size)
        if missing:
            self.stdout.write(self.style.WARNING(f'{missing} ta fayl topilmadi (--media-dir yoki --media-url ni tekshiring)'))

    def import_users(self):
        for r in self.rows('SELECT * FROM users ORDER BY id'):
            user = User.objects.filter(username__iexact=r['username']).first() or User(username=r['username'])
            user.name, user.email = r['name'] or r['username'], r['email'] or ''
            user.role, user.status = r['role'] or 'editor', r['status'] or 'active'
            user.position, user.department, user.scope = r['position'] or '', r['department'] or '', r['scope'] or ''
            user.hemis_id = r['hemis_id'] or ''
            user.avatar = self.m(r['avatar_id'])
            if r.get('salt') and r.get('hash'):
                # Payload paroli — foydalanuvchi o'z paroli bilan kiraveradi
                user.legacy_password = f"payload_pbkdf2$25000${r['salt']}${r['hash']}"
            user.save()
            self.stamp(User, user.pk, date_joined=r['created_at'])
            self.users[r['id']] = user

    def import_posts(self) -> int:
        cats = {}
        for r in self.rows('SELECT * FROM categories ORDER BY id'):
            cats[r['id']], _ = Category.objects.update_or_create(key=r['key'], defaults={'name': i18n(r, 'name')})
        texts = self.texts('posts_texts')
        attachments = self.children('posts_attachments')
        gallery: dict = {}
        for r in self.rows("SELECT parent_id, media_id FROM posts_rels WHERE path = 'gallery' ORDER BY parent_id, \"order\""):
            gallery.setdefault(r['parent_id'], []).append(r['media_id'])
        for r in self.rows('SELECT * FROM posts ORDER BY id'):
            tags = {lang: '\n'.join(texts.get((r['id'], f'tags.{lang}'), [])) for lang in LANGS}
            p = Post(
                type=r['type'], title=i18n(r, 'title'), excerpt=i18n(r, 'excerpt'), body=self.fix_i18n_html(i18n(r, 'body')),
                slug=r['slug'] or '', category=cats.get(r['category_id']), sdg=r['sdg'] or 0, cover=self.m(r['cover_id']),
                cover_ru=self.m(r['cover_by_lang_ru_id']), cover_en=self.m(r['cover_by_lang_en_id']), cover_zh=self.m(r['cover_by_lang_zh_id']),
                tags={k: v for k, v in tags.items() if v}, author=self.users.get(r['author_id']), published_at=r['published_at'],
                status=r['status'] or 'draft', hidden=bool(r['hidden']), starts_at=r['starts_at'], ends_at=r['ends_at'],
                location=i18n(r, 'location'), views=r['views'] or 0, deleted_at=r.get('deleted_at'),
            )
            p.save()
            self.stamp(Post, p.pk, created_at=r['created_at'], updated_at=r['updated_at'])
            for i, mid in enumerate(gallery.get(r['id'], [])):
                if self.m(mid):
                    PostGalleryImage.objects.create(post=p, image=self.m(mid), order=i)
            for i, a in enumerate(attachments.get(r['id'], [])):
                if self.m(a['file_id']):
                    PostAttachment.objects.create(post=p, file=self.m(a['file_id']), title=i18n(a, 'title'),
                                                  display=a['display'] or 'open', height=a['height'] or 680, order=i)
        return len(cats)

    def import_simple(self):
        for r in self.rows('SELECT * FROM slides ORDER BY "order", id'):
            if self.m(r['image_id']):
                Slide.objects.create(name=r['name'], image=self.m(r['image_id']), alt=i18n(r, 'alt'), link=r['link'] or '',
                                     starts_at=r['starts_at'], ends_at=r['ends_at'], order=r['order'] or 0)
        for r in self.rows('SELECT * FROM leaders ORDER BY "order", id'):
            Leader.objects.create(kind=r['kind'], name=r['name'], staff_id=r['staff_id'] or '', photo=self.m(r['photo_id']),
                                  role=i18n(r, 'role'), hours=i18n(r, 'hours'), phone=r['phone'] or '', ext=r['ext'] or '',
                                  email=r['email'] or '', reception=bool(r['reception']), order=r['order'] or 0)
        doc_cats = {r['id']: DocCategory.objects.create(title=i18n(r, 'title'), order=r['order'] or 0)
                    for r in self.rows('SELECT * FROM doc_categories ORDER BY "order", id')}
        texts = self.texts('documents_texts')
        for r in self.rows('SELECT * FROM documents ORDER BY "order", id'):
            d = Document(title=i18n(r, 'title'), category=doc_cats[r['category_id']], number=r['number'] or '', url=r['url'] or '',
                         display=r['display'] or 'open', height=r['height'] or 680, downloads=r['downloads'] or 0, order=r['order'] or 0,
                         pages=','.join(texts.get((r['id'], 'pages'), [])) or 'meyoriy-hujjatlar')
            for lang in LANGS:
                setattr(d, f'file_{lang}', self.m(r[f'files_{lang}_id']))
            d.save()
        vcats = {r['id']: VideoCategory.objects.update_or_create(key=r['key'], defaults={
            'title': i18n(r, 'title'), 'greeting': r['greeting'] or '', 'order': r['order'] or 0})[0]
            for r in self.rows('SELECT * FROM video_categories ORDER BY "order", id')}
        for r in self.rows('SELECT * FROM videos ORDER BY "order", id'):
            Video.objects.create(url=r['url'], title=i18n(r, 'title'), category=vcats[r['category_id']], teacher=r['teacher'] or '',
                                 duration=r['duration'] or '', thumbnail=r['thumbnail'] or '', order=r['order'] or 0)

    def import_structure(self):
        for r in self.rows('SELECT * FROM faculties ORDER BY "order", id'):
            Faculty.objects.update_or_create(slug=r['slug'], defaults={
                'name': i18n(r, 'name'), 'logo': self.m(r['logo_id']), 'cover': self.m(r['cover_id']), 'about': i18n(r, 'about'),
                'phone': r['phone'] or '', 'email': r['email'] or '', 'address': i18n(r, 'address'), 'map_url': r['map_url'] or '',
                'order': r['order'] or 0,
            })
        for r in self.rows('SELECT * FROM departments ORDER BY id'):
            Department.objects.update_or_create(hemis_id=r['hemis_id'], defaults={
                'faculty_slug': r['faculty'] or '', 'name': i18n(r, 'name'), 'image': self.m(r['image_id']), 'about': i18n(r, 'about'),
                'room': r['room'] or '', 'ext': r['ext'] or '', 'show_staff': bool(r['show_staff']),
            })
        nets = {'orcid': 'https://orcid.org/{}', 'scopus': 'https://www.scopus.com/authid/detail.uri?authorId={}', 'scholar': '{}', 'researchgate': '{}'}
        for r in self.rows('SELECT * FROM staff_profiles ORDER BY id'):
            science = [{'network': n, 'url': (r[n] if r[n].startswith('http') else tpl.format(r[n]))} for n, tpl in nets.items() if (r.get(n) or '').strip()]
            StaffProfile.objects.update_or_create(hemis_id=r['hemis_id'], defaults={
                'name': r['name'] or '', 'about': i18n(r, 'bio'), 'science': science, 'hidden': bool(r['hidden']),
            })

    def import_sdg(self):
        sections = self.children('sdg_goals_sections')
        reports = self.children('sdg_goals_reports')
        images: dict = {}
        for r in self.rows("SELECT parent_id, path, media_id FROM sdg_goals_rels ORDER BY parent_id, \"order\""):
            match = re.match(r'sections\.(\d+)\.images', r['path'] or '')
            if match:
                images.setdefault((r['parent_id'], int(match.group(1))), []).append(r['media_id'])
        for r in self.rows('SELECT * FROM sdg_goals ORDER BY n'):
            g, _ = SdgGoal.objects.update_or_create(n=r['n'], defaults={
                'title': i18n(r, 'title'), 'subtitle': i18n(r, 'subtitle'), 'url': r['url'], 'impact_rank': r['impact_rank'] or '',
                'impact_score': r['impact_score'] or '', 'highlight_label': r['highlight_label'] or '',
                'highlight_value': i18n(r, 'highlight_value'),
            })
            g.sections.all().delete()
            g.reports.all().delete()
            for i, s in enumerate(sections.get(r['id'], [])):
                sec = SdgSection.objects.create(goal=g, key=s['key'] or '', title=i18n(s, 'title') or {'uz': 'Bo‘lim'},
                                                body=self.fix_i18n_html(i18n(s, 'body')), order=i)
                sec.images.set([self.m(x) for x in images.get((r['id'], i), []) if self.m(x)])
            for i, a in enumerate(reports.get(r['id'], [])):
                if self.m(a['file_id']) or a['url']:
                    SdgGoalReport.objects.create(goal=g, file=self.m(a['file_id']), url=a['url'] or '', title=i18n(a, 'title'),
                                                 meta={'uz': a['meta']} if a.get('meta') else {}, display=a['display'] or 'open',
                                                 height=a['height'] or 680, order=i)
        page = self.rows('SELECT * FROM sdg_page LIMIT 1')
        if page:
            p = SdgPage.load()
            p.impact_year = page[0]['impact_year'] or p.impact_year
            p.save()

    def import_pages(self):
        facts, timeline, attachments = self.children('pages_facts'), self.children('pages_timeline'), self.children('pages_attachments')
        rows = self.rows('SELECT * FROM pages ORDER BY "order", id')
        pages = {}
        for r in rows:  # avval hammasi (ota sahifasiz), keyin bog'lanadi
            p = Page(title=i18n(r, 'title'), template=r['template'], slug=(r['slug'] or None) if r['template'] in ('text', 'group') else None,
                     url=r['url'] or '', file=self.m(r['file_id']), group_key=r['group_key'] or '', description=i18n(r, 'description'),
                     overview=r['overview'] or '', sdg=r['sdg'] or None, in_menu=bool(r['in_menu']), published=bool(r['published']),
                     highlight=bool(r['highlight']), lead=i18n(r, 'lead'), body=self.fix_i18n_html(i18n(r, 'body')), order=r['order'] or 0)
            if p.slug and Page.objects.filter(slug=p.slug).exists():
                p.slug = None
            p.save()
            pages[r['id']] = p
            for i, f in enumerate(facts.get(r['id'], [])):
                PageFact.objects.create(page=p, value=f['value'][:40], label=i18n(f, 'label'), order=i)
            for i, t in enumerate(timeline.get(r['id'], [])):
                PageTimeline.objects.create(page=p, label=i18n(t, 'label'), text=i18n(t, 'text'), highlight=bool(t['highlight']), order=i)
            for i, a in enumerate(attachments.get(r['id'], [])):
                if self.m(a['file_id']) or a['url']:
                    PageAttachment.objects.create(page=p, file=self.m(a['file_id']), url=a['url'] or '', title=i18n(a, 'title'),
                                                  meta=i18n(a, 'meta'), display=a['display'] or 'open', height=a['height'] or 680, order=i)
        for r in rows:
            if r['parent_id'] and r['parent_id'] in pages:
                Page.objects.filter(pk=pages[r['id']].pk).update(parent=pages[r['parent_id']])

    def import_globals(self):
        rows = self.rows('SELECT * FROM settings LIMIT 1')
        if rows:
            r = rows[0]
            s = SiteSettings.load()
            s.name, s.abbr, s.description = i18n(r, 'site_name') or s.name, i18n(r, 'site_abbr'), i18n(r, 'site_description')
            s.phone, s.email, s.address = r['contact_phone'] or s.phone, r['contact_email'] or '', i18n(r, 'contact_address')
            s.telegram, s.instagram = r['contact_telegram'] or '', r['contact_instagram'] or ''
            s.facebook, s.youtube = r['contact_facebook'] or '', r['contact_youtube'] or ''
            s.support_telegram, s.support_text = r['support_telegram'] or '', i18n(r, 'support_text')
            s.support_show_in_admin, s.support_show_on_site = bool(r['support_show_in_admin']), bool(r['support_show_on_site'])
            s.support_place = r['support_place'] or 'float'
            s.support_pages = ','.join(x['value'] for x in self.rows('SELECT value FROM settings_support_pages ORDER BY "order"'))
            s.numbers_auto = bool(r['numbers_auto'])
            s.students, s.staff, s.faculties, s.departments = r['numbers_students'], r['numbers_staff'], r['numbers_faculties'], r['numbers_departments']
            s.save()
        rows = self.rows('SELECT * FROM video_page LIMIT 1')
        if rows:
            r, v = rows[0], VideoPage.load()
            v.live, v.live_url, v.next_title, v.next_at = bool(r['live']), r['live_url'] or '', i18n(r, 'next_title'), r['next_at']
            v.channel_url = r['channel_url'] or v.channel_url
            v.save()
        rows = self.rows('SELECT * FROM symbols LIMIT 1')
        if rows:
            r = rows[0]
            for key in ('emblem', 'flag', 'anthem'):
                s = StateSymbol.objects.filter(key=key).first() or StateSymbol(key=key)
                s.image = self.m(r[f'{key}_image_id'])
                if key == 'anthem':
                    s.audio = self.m(r['anthem_audio_id'])
                s.title = i18n(r, f'{key}_title') or s.title
                s.description = i18n(r, f'{key}_description')
                s.link, s.source = r[f'{key}_link'] or '', r[f'{key}_source'] or ''
                s.save()

    def import_history(self):
        if Activity.objects.exists() or LoginEvent.objects.exists():
            return  # tarix bir marta ko'chiriladi
        for r in self.rows('SELECT * FROM activity ORDER BY id'):
            a = Activity.objects.create(user=self.users.get(r['user_id']), user_name=r['user_name'] or '', action=r['action'],
                                        entity=r['entity'], entity_id=r['entity_id'] or '', label=r['label'] or '',
                                        changes=r['changes'] or {}, ip=r['ip'] or '')
            self.stamp(Activity, a.pk, created_at=r['created_at'])
        for r in self.rows('SELECT * FROM login_events ORDER BY id'):
            e = LoginEvent.objects.create(user=self.users.get(r['user_id']), username=r['username'] or '', method=r['method'] or 'password',
                                          result=r['result'], ip=r['ip'] or '', network=r['network'] or '', browser=r['browser'] or '',
                                          os=r['os'] or '', device=r['device'] or '', user_agent=(r['user_agent'] or '')[:400])
            self.stamp(LoginEvent, e.pk, created_at=r['created_at'])
