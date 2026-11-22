"""Ikki parallel tarmoqni birlashtirish: 0005_campus_faculty (bino → fakultet) va 0008_rude_word (telefonlar, pasport, haqoratli so'zlar)."""
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('structure', '0005_campus_faculty'), ('structure', '0008_rude_word')]
    operations = []
