# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('plp_edmodule', '0008_auto_20161117_1242'),
    ]

    operations = [
        migrations.CreateModel(
            name='Benefit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=160, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435')),
                ('description', models.TextField(default=b'', blank=True, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', validators=[django.core.validators.MaxLengthValidator(400)])),
                ('icon', models.ImageField(help_text='png, \u0440\u0430\u0437\u043c\u0435\u0440 \u0444\u0430\u0439\u043b\u0430 \u043d\u0435 \u0431\u043e\u043b\u0435\u0435 1 \u043c\u0431, \u0440\u0430\u0437\u0440\u0435\u0448\u0435\u043d\u0438\u0435 \u043d\u0435 \u0431\u043e\u043b\u0435\u0435 1000*1000', upload_to=b'benefit_icons', verbose_name='\u0418\u043a\u043e\u043d\u043a\u0430')),
            ],
            options={
                'verbose_name': '\u0412\u044b\u0433\u043e\u0434\u0430',
                'verbose_name_plural': '\u0412\u044b\u0433\u043e\u0434\u044b',
            },
        ),
        migrations.CreateModel(
            name='BenefitLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField(verbose_name='\u041e\u0431\u044a\u0435\u043a\u0442, \u043a \u043a\u043e\u0442\u043e\u0440\u043e\u043c\u0443 \u0432\u044b\u0433\u043e\u0434\u0430')),
                ('benefit', models.ForeignKey(related_name='benefit_links', verbose_name='\u0412\u044b\u0433\u043e\u0434\u0430', to='plp_edmodule.Benefit')),
                ('content_type', models.ForeignKey(verbose_name='\u0422\u0438\u043f \u043e\u0431\u044a\u0435\u043a\u0442\u0430, \u043a \u043a\u043e\u0442\u043e\u0440\u043e\u043c\u0443 \u0432\u044b\u0433\u043e\u0434\u0430', to='contenttypes.ContentType')),
            ],
        ),
    ]
