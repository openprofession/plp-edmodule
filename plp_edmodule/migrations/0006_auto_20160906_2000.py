# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plp_edmodule', '0005_auto_20160903_0401'),
    ]

    operations = [
        migrations.AlterField(
            model_name='educationalmodule',
            name='cover',
            field=models.ImageField(help_text='\u041c\u0438\u043d\u0438\u043c\u0443\u043c 345*220, \u043a\u0430\u0440\u0442\u0438\u043d\u043a\u0438 \u0431\u043e\u043b\u044c\u0448\u0435\u0433\u043e \u0440\u0430\u0437\u043c\u0435\u0440\u0430 \u0431\u0443\u0434\u0443\u0442 \u0441\u0436\u0430\u0442\u044b \u0434\u043e \u044d\u0442\u043e\u0433\u043e \u0440\u0430\u0437\u043c\u0435\u0440\u0430', upload_to=b'edmodule_cover', verbose_name='\u041e\u0431\u043b\u043e\u0436\u043a\u0430 EM', blank=True),
        ),
    ]
