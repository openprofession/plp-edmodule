# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plp_edmodule', '0013_auto_20170919_1816'),
    ]

    operations = [
        migrations.AddField(
            model_name='educationalmodule',
            name='offer_text',
            field=models.TextField(default=b'', help_text='HTML \u0431\u043b\u043e\u043a', verbose_name='\u0422\u0435\u043a\u0441\u0442 \u043e\u0444\u0435\u0440\u0442\u044b', blank=True),
        ),
    ]
