# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plp_edmodule', '0012_promocode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coursepromotion',
            name='sort',
            field=models.SmallIntegerField(verbose_name='\u041f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442'),
        ),
        migrations.AlterField(
            model_name='promocode',
            name='course',
            field=models.ForeignKey(verbose_name='\u041a\u0443\u0440\u0441', blank=True, to='plp.Course', null=True),
        ),
    ]
