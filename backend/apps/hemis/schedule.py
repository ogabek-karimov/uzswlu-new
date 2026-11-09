"""Kechki jadval: og'ir ishlar (HEMIS sinxronlash va b.) faqat «tinch oyna»da — server ham, HEMIS ham bo'sh vaqtda.

Hamma funksiya sof (soat/sozlamalarga bog'liq emas) — alohida sinaladi. Vaqt — mahalliy (TIME_ZONE) aware datetime.
"""
import random
from datetime import date, datetime, time, timedelta


def parse_time(value: str) -> time:
    h, m = value.strip().split(':')
    return time(int(h), int(m))


def parse_window(value: str) -> tuple[time, time]:
    start, end = value.split('-')
    return parse_time(start), parse_time(end)


def in_window(now: datetime, window: tuple[time, time]) -> bool:
    """Oyna yarim tunni kesib o'tishi mumkin (masalan 23:00-04:00)."""
    start, end = window
    t = now.timetz().replace(tzinfo=None)
    return start <= t < end if start <= end else (t >= start or t < end)


def window_end(now: datetime, window: tuple[time, time]) -> datetime:
    """`now` shu oynada bo'lsa — oyna tugaydigan lahza."""
    start, end = window
    end_dt = now.replace(hour=end.hour, minute=end.minute, second=0, microsecond=0)
    return end_dt if end_dt > now else end_dt + timedelta(days=1)


def run_time(day: date, at: time, jitter_minutes: int, window: tuple[time, time], tz) -> datetime:
    """Kunning ishga tushish vaqti: `at` + shu kunga xos tasodifiy kechikish (restartdan keyin ham bir xil —
    qayta ishga tushirish sinxronlashni «yaqinlashtirib» yubormaydi). Oyna ichida qoladi."""
    jitter = random.Random(day.isoformat()).uniform(0, max(0, jitter_minutes))
    start, end = window
    base = datetime.combine(day, at, tzinfo=tz) + timedelta(minutes=jitter)
    latest = datetime.combine(day, end, tzinfo=tz) - timedelta(minutes=1)
    if end <= start:  # yarim tundan o'tuvchi oyna: tugash ertasi kuni
        latest += timedelta(days=1)
    return min(base, latest)


def next_run(now: datetime, at: time, jitter_minutes: int, window: tuple[time, time]) -> datetime:
    """Eng yaqin kelajakdagi ishga tushish vaqti."""
    for offset in (0, 1):
        candidate = run_time(now.date() + timedelta(days=offset), at, jitter_minutes, window, now.tzinfo)
        if candidate > now:
            return candidate
    return run_time(now.date() + timedelta(days=2), at, jitter_minutes, window, now.tzinfo)  # pragma: no cover
