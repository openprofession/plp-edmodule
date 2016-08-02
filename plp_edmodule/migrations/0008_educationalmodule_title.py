# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plp_edmodule', '0007_module_enrollment_type_and_reason'),
    ]

    operations = [
        migrations.AddField(
            model_name='educationalmodule',
            name='title',
            field=models.CharField(default='', max_length=200, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435'),
            preserve_default=False,
        ),
    ]
