# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import sortedm2m.fields
import sortedm2m.operations


class Migration(migrations.Migration):

    dependencies = [
        ('plp_edmodule', '0003_count_rating_on_educationalmodule'),
    ]

    operations = [
        sortedm2m.operations.AlterSortedManyToManyField(
            model_name='educationalmodule',
            name='courses',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, related_name='education_modules', verbose_name='\u041a\u0443\u0440\u0441\u044b', to='plp.Course'),
        ),
    ]
