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
            name='status',
            field=models.CharField(default=b'hidden', max_length=16, verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441', choices=[(b'hidden', '\u0421\u043a\u0440\u044b\u0442'), (b'published', '\u041e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u043d')]),
        ),
    ]
