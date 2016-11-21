# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plp_edmodule', '0007_educationalmoduleenrollmentreason_full_paid'),
    ]

    operations = [
        migrations.AddField(
            model_name='educationalmodule',
            name='subtitle',
            field=models.TextField(default=b'', help_text='\u043e\u0442 1 \u0434\u043e 3 \u044d\u043b\u0435\u043c\u0435\u043d\u0442\u043e\u0432, \u043a\u0430\u0436\u0434\u044b\u0439 \u0441 \u043d\u043e\u0432\u043e\u0439 \u0441\u0442\u0440\u043e\u043a\u0438', verbose_name='\u041f\u043e\u0434\u0437\u0430\u0433\u043e\u043b\u043e\u0432\u043e\u043a', blank=True),
        ),
        migrations.AddField(
            model_name='educationalmodule',
            name='vacancies',
            field=models.TextField(default=b'', help_text='HTML \u0431\u043b\u043e\u043a', verbose_name='\u0412\u0430\u043a\u0430\u043d\u0441\u0438\u0438', blank=True),
        ),
    ]
