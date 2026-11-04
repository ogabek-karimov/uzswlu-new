"""So'rovdan IP, tarmoq turi, brauzer, OS va qurilma (kirish tarixi uchun, kutubxonasiz)."""
import re

from apps.core.utils import client_ip


def network_of(ip: str) -> str:
    if ip in ('127.0.0.1', '::1'):
        return 'localhost'
    if re.match(r'^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)', ip):
        return 'Ichki tarmoq'
    return 'Internet'


def _ver(pattern: str, ua: str):
    m = re.search(pattern, ua)
    return m.group(1) if m else None


def parse_user_agent(ua: str) -> dict:
    browser = (
        f"Edge {_ver(r'Edg/(\d+)', ua)}" if _ver(r'Edg/(\d+)', ua)
        else f"Opera {_ver(r'OPR/(\d+)', ua)}" if _ver(r'OPR/(\d+)', ua)
        else f"Firefox {_ver(r'Firefox/(\d+)', ua)}" if _ver(r'Firefox/(\d+)', ua)
        else f"Chrome {_ver(r'Chrome/(\d+)', ua)}" if _ver(r'Chrome/(\d+)', ua)
        else f"Safari {_ver(r'Version/(\d+).*Safari', ua)}" if _ver(r'Version/(\d+).*Safari', ua)
        else (_ver(r'^([\w-]+)/[\d.]+', ua) or 'Nomaʼlum')
    )
    os_ = (
        'Windows 10/11' if 'Windows NT 10' in ua
        else 'Windows' if 'Windows' in ua
        else 'iOS' if re.search(r'iPhone|iPad', ua)
        else f"Android {_ver(r'Android (\d+)', ua)}" if _ver(r'Android (\d+)', ua)
        else 'macOS' if 'Mac OS X' in ua
        else 'Linux' if 'Linux' in ua
        else 'Nomaʼlum'
    )
    device = 'Planshet' if re.search(r'iPad|Tablet', ua) else 'Telefon' if re.search(r'Mobile|iPhone|Android', ua) else 'Kompyuter'
    return {'browser': browser[:60], 'os': os_, 'device': device}


def request_info(request) -> dict:
    ip = client_ip(request).replace('::ffff:', '') or 'nomaʼlum'
    if ip == '::1':
        ip = '127.0.0.1'
    ua = (request.META.get('HTTP_USER_AGENT') or '')[:400]
    return {'ip': ip, 'network': network_of(ip), 'user_agent': ua, **parse_user_agent(ua)}
