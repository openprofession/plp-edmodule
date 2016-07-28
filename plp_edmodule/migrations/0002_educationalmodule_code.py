# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plp_edmodule', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='educationalmodule',
            name='code',
            field=models.SlugField(default=None, unique=True, verbose_name='\u041a\u043e\u0434'),
            preserve_default=False,
        ),
    ]
