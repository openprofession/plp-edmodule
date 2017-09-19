# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('specproject', '0001_initial'),
        ('plp_edmodule', '0012_promocode'),
    ]

    operations = [
        migrations.AddField(
            model_name='coursepromotion',
            name='spec_project',
            field=models.ForeignKey(default=None, blank=True, to='specproject.SpecProject', null=True, verbose_name='\u041f\u0440\u0435\u0434\u0441\u0442\u0430\u0432\u043b\u0435\u043d\u0438\u0435'),
        ),
        migrations.AddField(
            model_name='educationalmodule',
            name='spec_projects',
            field=models.ManyToManyField(to='specproject.SpecProject', verbose_name='\u041f\u0440\u0435\u0434\u0441\u0442\u0430\u0432\u043b\u0435\u043d\u0438\u0435', blank=True),
        ),
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
        migrations.AlterUniqueTogether(
            name='coursepromotion',
            unique_together=set([('sort', 'spec_project')]),
        ),
    ]
