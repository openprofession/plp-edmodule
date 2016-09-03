# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plp_edmodule', '0004_sortable_courses_on_educationalmodule'),
    ]

    operations = [
        migrations.AlterField(
            model_name='educationalmodulerating',
            name='status',
            field=models.CharField(default=b'published', max_length=15, verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441', choices=[(b'published', '\u041e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u043d\u043e'), (b'waiting', '\u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435'), (b'hidden_by_user', '\u0423\u0434\u0430\u043b\u0435\u043d\u043e \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u043c')]),
        ),
    ]
