# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('plp_edmodule', '0009_benefit_benefitlink'),
    ]

    operations = [
        migrations.CreateModel(
            name='CoursePromotion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField(verbose_name='Id \u043e\u0431\u044a\u0435\u043a\u0442\u0430')),
                ('sort', models.SmallIntegerField(unique=True, verbose_name='\u041f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442')),
                ('content_type', models.ForeignKey(verbose_name='\u0422\u0438\u043f \u043e\u0431\u044a\u0435\u043a\u0442\u0430', to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ['sort'],
                'verbose_name': '\u041f\u043e\u0440\u044f\u0434\u043e\u043a \u043a\u0443\u0440\u0441\u043e\u0432 \u0438 \u0441\u043f\u0435\u0446\u0438\u0430\u043b\u0438\u0437\u0430\u0446\u0438\u0439 \u043d\u0430 \u0433\u043b\u0430\u0432\u043d\u043e\u0439',
                'verbose_name_plural': '\u041f\u043e\u0440\u044f\u0434\u043e\u043a \u043a\u0443\u0440\u0441\u043e\u0432 \u0438 \u0441\u043f\u0435\u0446\u0438\u0430\u043b\u0438\u0437\u0430\u0446\u0438\u0439 \u043d\u0430 \u0433\u043b\u0430\u0432\u043d\u043e\u0439',
            },
        ),
    ]
