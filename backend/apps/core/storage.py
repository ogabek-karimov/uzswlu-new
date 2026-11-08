"""Yopiq saqlash: ochiq `/media/` dan tashqarida turadigan fayllar (fuqarolar murojaati ilovalari).

Fayllar `PRIVATE_ROOT` da, URL esa faqat autentifikatsiyali endpoint orqali: `/api/cms/private/<yo'l>`.
"""
from django.conf import settings
from django.core.files.storage import FileSystemStorage


def private_storage() -> FileSystemStorage:
    # Chaqiriladigan (callable) — migratsiyada yo'l qotib qolmaydi
    return FileSystemStorage(location=settings.PRIVATE_ROOT, base_url='/api/cms/private/')
