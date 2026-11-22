"""Saytdagi barcha o'zbekcha (uz) matnlar — yangi alifboda: Oʻ→Ö, Gʻ→Ğ, Sh→Ş, Ch→Ç (apps.core.alphabet).

Har bir modelning I18nField maydonlaridagi «uz» qiymati o'giriladi (menyu = sahifa sarlavhalari, sahifalar, yangiliklar,
e'lonlar, hujjatlar, lavozimlar, BRM, qabul…). Jurnallar (Activity, Hit, Version, LoginEvent), haqoratli so'zlar,
HEMIS nusxasi va odamlarning F.I.Sh. (CharField) tegilmaydi. Takror ishlatilsa ham xavfsiz."""
from django.db import migrations

from apps.core.alphabet import to_new_alphabet
from apps.core.fields import I18nField

SKIP = {'core.Activity', 'core.Hit', 'panel.Version', 'panel.LoginEvent', 'structure.RudeWord', 'hemis.HemisSnapshot'}


def forward(apps, schema_editor):
    for model in apps.get_models():
        if model._meta.label in SKIP:
            continue
        names = [f.name for f in model._meta.fields if isinstance(f, I18nField)]
        if not names:
            continue
        for obj in model.objects.all().only('pk', *names):
            changed = []
            for name in names:
                value = getattr(obj, name)
                if isinstance(value, dict) and isinstance(value.get('uz'), str):
                    new = to_new_alphabet(value['uz'])
                    if new != value['uz']:
                        setattr(obj, name, {**value, 'uz': new})
                        changed.append(name)
            if changed:
                obj.save(update_fields=changed)


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0006_sitesettings_show_buildings_link'),
        ('content', '0009_unit_heads'),
        ('structure', '0010_admission_years'),
        ('pages', '0011_uz_new_alphabet'),
        ('accounts', '0008_hemis_role'),
    ]
    operations = [migrations.RunPython(forward, migrations.RunPython.noop)]
