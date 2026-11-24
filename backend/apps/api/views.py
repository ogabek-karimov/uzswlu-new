"""Ochiq sayt API'si (frontend/docs/openapi.yaml). Hamma javob `?lang=uz|ru|en|zh` bo'yicha."""
import json
import re

from datetime import timedelta

from django.core.cache import cache
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from rest_framework.exceptions import NotFound, Throttled
from rest_framework.response import Response

from apps.content.models import Document, Leader, Post
from apps.core.uploads import clean_upload
from apps.core.throttles import ScopedThrottle
from apps.core.utils import client_ip, sha256
from apps.pages.models import Page, SdgGoal
from apps.structure.models import Appeal, Application, Faculty
from apps.api.text_quality import is_meaningful_text

from . import builders, builders_site as bs, search
from .builders_staff import Unprocessable
from .common import OpenView, PublicView, lang_of
from .hits import record_hit


def _int(value, default: int, lo: int, hi: int) -> int:
    try:
        return min(hi, max(lo, int(value)))
    except (TypeError, ValueError):
        return default


class HomeView(PublicView):
    def get(self, request):
        return Response(bs.home_out(lang_of(request)))


class SiteView(PublicView):
    def get(self, request):
        return Response(bs.site_out(lang_of(request)))


class MenuView(PublicView):
    def get(self, request):
        return Response(bs.menu_out(lang_of(request)))


class SettingsView(PublicView):
    def get(self, request):
        return Response(bs.settings_out(lang_of(request)))


class SymbolsView(PublicView):
    def get(self, request):
        return Response(bs.symbols_out(lang_of(request)))


class SlidesView(PublicView):
    def get(self, request):
        return Response(bs.slides_out(lang_of(request)))


class PageView(PublicView):
    def get(self, request, slug):
        page = Page.objects.filter(slug=slug, template='text', published=True).first()
        if not page:
            raise NotFound('Page not found')
        return Response(bs.page_out(page, lang_of(request)))


class PostListView(PublicView):
    def get(self, request):
        p = request.query_params
        type_ = p.get('type') if p.get('type') in bs.POST_TYPES else 'news'
        return Response(bs.posts_list_out(
            lang_of(request),
            type_=type_,
            q=(p.get('q') or '').strip()[:100],
            month=p.get('month'),
            sdg=_int(p.get('sdg'), 0, 0, 17),
            page=_int(p.get('page'), 1, 1, 100_000),
            per_page=_int(p.get('perPage'), 12, 1, 48),
        ))


class PostDetailView(PublicView):
    def get(self, request, type, slug):  # noqa: A002 — URL parametri nomi shartnomadagidek
        lang = lang_of(request)
        if type not in bs.POST_TYPES:
            raise NotFound('Post not found')
        post = (
            Post.visible(lang).filter(type=type, slug=slug)
            .select_related(*builders.POST_RELATED, 'author', 'author__avatar').first()
        )
        if not post:
            raise NotFound('Post not found')
        return Response(builders.post_detail(post, lang))


class LatestView(PublicView):
    """Payload bilan mos: /site/latest."""

    def get(self, request):
        lang = lang_of(request)
        return Response({
            'news': [builders.news_item(p, lang) for p in builders.latest_posts(lang, 'news', 4)],
            'announcements': [builders.announcement_item(p, lang) for p in builders.latest_posts(lang, 'announcements', 5)],
            'events': [builders.event_item(p, lang) for p in builders.upcoming_events(lang, 3)],
        })


class PostIndexView(PublicView):
    """Payload bilan mos: /site/index."""

    def get(self, request):
        return Response(bs.post_index_out(lang_of(request)))


class EventsView(PublicView):
    def get(self, request):
        month = request.query_params.get('month') or ''
        if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', month):
            month = bs.current_month()
        return Response(bs.events_out(lang_of(request), month))


class LeadershipView(PublicView):
    def get(self, request):
        return Response(bs.leadership_out(lang_of(request)))


class DocumentsView(PublicView):
    def get(self, request):
        return Response(bs.documents_out(lang_of(request), request.query_params.get('page') or None))


class DocumentFileView(OpenView):
    """PDF manzili o'zgarmaydi: yangi versiya yuklansa ham shu havola yangisini beradi. Yuklab olishlar soni oshadi."""

    def get(self, request, pk):
        lang = lang_of(request)
        doc = Document.objects.select_related('file_uz', 'file_ru', 'file_en', 'file_zh').filter(pk=pk).first()
        file = doc.file_for(lang) if doc else None
        if not file:
            raise NotFound('File not found')
        if cache.add(f'dl:{pk}:{sha256(client_ip(request))[:16]}', 1, 3600):  # bir IP bir soatda bir marta hisoblanadi (hisobni sun'iy oshirib bo'lmasin)
            Document.objects.filter(pk=pk).update(downloads=F('downloads') + 1)
        try:
            record_hit(request, {'kind': 'event', 'name': 'PDF yuklab olindi', 'value': str(pk), 'lang': lang})
        except Exception:  # noqa: BLE001 — statistika yuklab olishni to'xtatmasin
            pass
        return HttpResponseRedirect(file.url)


class ProgramsView(PublicView):
    def get(self, request):
        level = request.query_params.get('level')
        return Response(bs.programs_out(lang_of(request), level if level in ('bachelor', 'master') else 'bachelor'))


class FacultyListView(PublicView):
    def get(self, request):
        return Response(bs.faculties_out(lang_of(request)))


class FacultyDetailView(PublicView):
    def get(self, request, slug):
        faculty = Faculty.objects.select_related('logo').filter(slug=slug).first()
        if not faculty:
            raise NotFound('Faculty not found')
        return Response(bs.faculty_out(faculty, lang_of(request)))


class AdmissionView(PublicView):
    """?year=2025-2026 — saytda ko'rinadigan arxiv yili; berilmasa — faol yil."""

    def get(self, request):
        year = str(request.query_params.get('year') or '').strip()
        if year and not re.fullmatch(r'\d{4}-\d{4}', year):
            raise NotFound('Admission year not found')
        data = bs.admission_out(lang_of(request), year or None)
        if data is None:
            raise NotFound('Admission year not found')
        return Response(data)


class SdgOverviewView(PublicView):
    def get(self, request):
        return Response(bs.sdg_overview_out(lang_of(request)))


class SdgGoalsView(PublicView):
    """Payload bilan mos: /site/sdg-goals."""

    def get(self, request):
        return Response(bs.sdg_goals_out(lang_of(request)))


class SdgGoalView(PublicView):
    def get(self, request, n):
        goal = SdgGoal.objects.filter(n=n).first()
        if not goal:
            raise NotFound('Goal not found')
        return Response(bs.sdg_goal_out(goal, lang_of(request)))


class VideosView(PublicView):
    def get(self, request):
        return Response(bs.videos_out(lang_of(request)))


class ContactView(PublicView):
    def get(self, request):
        return Response(bs.contact_out(lang_of(request)))


class SearchView(PublicView):
    throttle_scope = 'search'

    def get(self, request):
        p = request.query_params
        q = (p.get('q') or '').strip()[:100]
        page = _int(p.get('page'), 1, 1, 500)
        per_page = _int(p.get('perPage'), 10, 1, 50)
        if not q:
            return Response({'q': q, 'counts': dict.fromkeys(search.KINDS, 0), 'quick': None, 'items': [], 'total': 0, 'page': page, 'perPage': per_page})
        kind = p.get('type') if p.get('type') in search.KINDS else None
        return Response(search.search_out(lang_of(request), q, kind, page, per_page))


APPEAL_FILE_TYPES = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'}
APPEAL_MAX_FILE = 10 * 1024 * 1024


class AppealView(PublicView):
    """Virtual qabulxona murojaati. Frontend serveri tekshirgan, backend ham tekshiradi va spamdan himoya qiladi."""

    throttle_classes = [ScopedThrottle]
    throttle_scope = 'appeals'

    def post(self, request):
        d = request.data
        name, phone, email = (str(d.get(k) or '').strip() for k in ('name', 'phone', 'email'))
        recipient, message = str(d.get('recipient') or '').strip(), str(d.get('message') or '').strip()
        if not 3 <= len(name) <= 200:
            raise Unprocessable('Invalid name')
        passport = re.sub(r'\s', '', str(d.get('passport') or '')).upper()
        if not re.fullmatch(r'[A-Z]{2}\d{7}', passport):
            raise Unprocessable('Invalid passport')
        if not re.fullmatch(r'\+?[\d\s()-]{7,20}', phone):
            raise Unprocessable('Invalid phone')
        if len(email) > 200 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
            raise Unprocessable('Invalid email')
        if not re.fullmatch(r'[\w-]{1,40}', recipient):
            raise Unprocessable('Invalid recipient')
        if not 10 <= len(message) <= 5000 or not is_meaningful_text(message):
            raise Unprocessable('Invalid message')
        if str(d.get('consent') or '') != 'yes':
            raise Unprocessable('Consent required')
        day_ago = timezone.now() - timedelta(days=1)
        if Appeal.objects.filter(email__iexact=email, created_at__gte=day_ago).count() >= 3:
            raise Throttled(detail='Too many appeals')
        file = request.FILES.get('file')
        if file:
            try:
                file, _ = clean_upload(file, APPEAL_FILE_TYPES, APPEAL_MAX_FILE)  # tozalangan nusxa, tasodifiy nom
            except ValidationError as exc:
                raise Unprocessable('Invalid file') from exc

        title = recipient
        m = re.fullmatch(r'leader-(\d+)', recipient)
        if m:
            leader = Leader.objects.filter(pk=m.group(1)).first()
            title = leader.role.get('uz', recipient) if leader else recipient
        appeal = Appeal.objects.create(
            name=name, passport=passport, phone=phone, email=email, recipient=recipient, recipient_title=title[:300],
            message=message, ip=client_ip(request),
        )
        if file:
            appeal.file = file
            appeal.save(update_fields=['file'])
        return Response({'number': appeal.number})


APPLICATION_FILE_TYPES = {'.pdf', '.jpg', '.jpeg', '.png'}
APPLICATION_MAX_FILE = 5 * 1024 * 1024


class ApplicationView(PublicView):
    """Xorijiy abituriyent arizasi (pasport, diplom/sertifikat va 3x4 surat — majburiy). Frontend serveri ham tekshiradi."""

    throttle_classes = [ScopedThrottle]
    throttle_scope = 'appeals'

    def post(self, request):
        d = request.data
        f = {k: re.sub(r'\s+', ' ', str(d.get(k) or '')).strip() for k in (
            'lastName', 'firstName', 'middleName', 'passport', 'country', 'address', 'gender', 'faculty', 'studyForm', 'degree', 'program', 'phone', 'email', 'lang')}
        f['passport'] = f['passport'].replace(' ', '').upper()
        checks = [
            2 <= len(f['lastName']) <= 70, 2 <= len(f['firstName']) <= 60, len(f['middleName']) <= 60,
            re.fullmatch(r'[A-Z0-9]{5,20}', f['passport']), 2 <= len(f['country']) <= 80, 5 <= len(f['address']) <= 300,
            f['gender'] in dict(Application.GENDERS), 2 <= len(f['faculty']) <= 200, f['studyForm'] in dict(Application.FORMS),
            f['degree'] in dict(Application.DEGREES), 2 <= len(f['program']) <= 300,
            re.fullmatch(r'\+?[\d\s()-]{7,20}', f['phone']), len(f['email']) <= 200 and re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', f['email']),
        ]
        if not all(checks):
            raise Unprocessable('Invalid form')
        if str(d.get('consent') or '') != 'yes':
            raise Unprocessable('Consent required')
        day_ago = timezone.now() - timedelta(days=1)
        if Application.objects.filter(email__iexact=f['email'], created_at__gte=day_ago).count() >= 3:
            raise Throttled(detail='Too many applications')
        files = {}
        for key in ('passportFile', 'diplomaFile', 'photoFile'):
            up = request.FILES.get(key)
            if not up:
                raise Unprocessable('File required')
            try:
                files[key], _ = clean_upload(up, APPLICATION_FILE_TYPES, APPLICATION_MAX_FILE)
            except ValidationError as exc:
                raise Unprocessable('Invalid file') from exc
        a = Application.objects.create(
            last_name=f['lastName'], first_name=f['firstName'], middle_name=f['middleName'], passport=f['passport'], country=f['country'],
            address=f['address'], gender=f['gender'], faculty=f['faculty'], study_form=f['studyForm'], degree=f['degree'], program=f['program'],
            phone=f['phone'], email=f['email'], lang=f['lang'] if f['lang'] in ('uz', 'ru', 'en', 'zh') else 'uz', ip=client_ip(request),
            passport_file=files['passportFile'], diploma_file=files['diplomaFile'], photo_file=files['photoFile'],
        )
        return Response({'number': a.number})


class HitView(OpenView):
    """Statistika yozuvi. Hech qachon xato qaytarmaydi (sendBeacon `text/plain` yuboradi)."""

    throttle_classes = [ScopedThrottle]
    throttle_scope = 'hit'

    def post(self, request):
        try:
            data = json.loads(request.body or b'{}')
            if isinstance(data, dict):
                record_hit(request, data)
        except Exception:  # noqa: BLE001
            pass
        return Response(status=204)
