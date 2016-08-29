# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plp_edmodule', '0002_educationalmodule_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='educationalmodule',
            name='count_ratings',
            field=models.PositiveIntegerField(default=0, verbose_name='\u041a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e \u043e\u0446\u0435\u043d\u043e\u043a'),
        ),
        migrations.AddField(
            model_name='educationalmodule',
            name='sum_ratings',
            field=models.PositiveIntegerField(default=0, verbose_name='\u0421\u0443\u043c\u043c\u0430 \u043e\u0446\u0435\u043d\u043e\u043a'),
        ),
    ]
