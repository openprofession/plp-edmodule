# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('plp_edmodule', '0003_educationalmoduleenrollment'),
    ]

    operations = [
        migrations.CreateModel(
            name='EducationalModuleProgress',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('progress', jsonfield.fields.JSONField(null=True, verbose_name='\u041f\u0440\u043e\u0433\u0440\u0435\u0441\u0441')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='\u0412\u0440\u0435\u043c\u044f \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0435\u0433\u043e \u043e\u0431\u0440\u0430\u0449\u0435\u043d\u0438\u044f \u043a edx')),
                ('enrollment', models.OneToOneField(related_name='progress', verbose_name='\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0430 \u043c\u043e\u0434\u0443\u043b\u044c', to='plp_edmodule.EducationalModuleEnrollment')),
            ],
            options={
                'verbose_name': '\u041f\u0440\u043e\u0433\u0440\u0435\u0441\u0441 \u043f\u043e \u043c\u043e\u0434\u0443\u043b\u044e',
                'verbose_name_plural': '\u041f\u0440\u043e\u0433\u0440\u0435\u0441\u0441 \u043f\u043e \u043c\u043e\u0434\u0443\u043b\u044f\u043c',
            },
        ),
    ]
