# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plp_edmodule', '0008_educationalmodule_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='educationalmodule',
            name='cover',
            field=models.ImageField(upload_to=b'edmodule_cover', verbose_name='\u041e\u0431\u043b\u043e\u0436\u043a\u0430', blank=True),
        ),
    ]
