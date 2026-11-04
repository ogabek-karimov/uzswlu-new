"""HEMIS (faqat o'qish) klienti interfeysi.

HEMIS API ulanganda shu interfeysni amalga oshiruvchi klass yoziladi va `HEMIS_CLIENT` sozlamasiga qo'yiladi —
API ko'rinishlari o'zgarmaydi. Qaytariladigan tuzilmalar quyida tavsiflangan.
"""
from abc import ABC, abstractmethod
from datetime import datetime


class HemisClient(ABC):
    @abstractmethod
    def synced_at(self) -> datetime | None:
        """Oxirgi sinxronlash vaqti; None — HEMIS hali ulanmagan (namuna ma'lumot)."""

    @abstractmethod
    def summary(self) -> dict:
        """{'faculties': int, 'departments': int}"""

    @abstractmethod
    def faculties(self) -> list[dict]:
        """Fakultetlar (HEMIS qismi): slug, order, logo, name{lang}, about{lang}, stats{students,departments,programs,teachers},
        dean{lang: {...}}, deanery{lang: [...]}, programs{lang: [...]}, departments[{id, head, name{lang}}],
        contact{lang: {address, phone, email, mapUrl}}."""

    @abstractmethod
    def staff(self, lang: str) -> list[dict]:
        """Barcha xodimlar: id, name, patronymic, photo, group (lead|faculty|chair|unit),
        employments[{department{id,name}, position{code,name}, form, rate, status, type}] — HEMIS tartibida."""

    @abstractmethod
    def staff_departments(self, lang: str) -> list[dict]:
        """Xodim bo'limlari: id, name, group, count."""

    @abstractmethod
    def person(self, hemis_id: str) -> dict | None:
        """Shaxsiy ma'lumot (kabinet): firstName, lastName, patronymic, birthDate, phone, email."""

    def faculty(self, slug: str) -> dict | None:
        return next((f for f in self.faculties() if f['slug'] == slug), None)
