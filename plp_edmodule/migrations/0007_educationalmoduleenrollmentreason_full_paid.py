# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plp_edmodule', '0006_auto_20160906_2000'),
    ]

    operations = [
        migrations.AddField(
            model_name='educationalmoduleenrollmentreason',
            name='full_paid',
            field=models.BooleanField(default=True, verbose_name='\u0421\u043f\u0435\u0446\u0438\u0430\u043b\u0438\u0437\u0430\u0446\u0438\u044f \u043e\u043f\u043b\u0430\u0447\u0435\u043d\u0430 \u043f\u043e\u043b\u043d\u043e\u0441\u0442\u044c\u044e'),
        ),
    ]
