# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('plp_edmodule', '0002_educationalmodule_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='EducationalModuleEnrollment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('module', models.ForeignKey(verbose_name='\u041e\u0431\u0440\u0430\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c\u043d\u044b\u0439 \u043c\u043e\u0434\u0443\u043b\u044c', to='plp_edmodule.EducationalModule')),
                ('user', models.ForeignKey(verbose_name='\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0430 \u043c\u043e\u0434\u0443\u043b\u044c',
                'verbose_name_plural': '\u0417\u0430\u043f\u0438\u0441\u0438 \u043d\u0430 \u043c\u043e\u0434\u0443\u043b\u044c',
            },
        ),
        migrations.AlterUniqueTogether(
            name='educationalmoduleenrollment',
            unique_together=set([('user', 'module')]),
        ),
    ]
