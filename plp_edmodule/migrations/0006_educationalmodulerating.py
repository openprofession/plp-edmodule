# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('plp_edmodule', '0005_educationalmoduleunsubscribe'),
    ]

    operations = [
        migrations.CreateModel(
            name='EducationalModuleRating',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField(verbose_name='Id \u043e\u0431\u044a\u0435\u043a\u0442\u0430 \u043e\u0442\u0437\u044b\u0432\u0430')),
                ('rating', models.PositiveSmallIntegerField(verbose_name='\u041e\u0446\u0435\u043d\u043a\u0430')),
                ('comment', models.TextField(default=b'', verbose_name='\u041f\u043e\u044f\u0441\u043d\u0435\u043d\u0438\u0435', blank=True)),
                ('pros', models.TextField(default=b'', null=True, verbose_name='\u0414\u043e\u0441\u0442\u043e\u0438\u043d\u0441\u0442\u0432\u0430', blank=True)),
                ('cons', models.TextField(default=b'', null=True, verbose_name='\u041d\u0435\u0434\u043e\u0441\u0442\u0430\u0442\u043a\u0438', blank=True)),
                ('declined', models.BooleanField(default=False, verbose_name='\u041e\u0442\u0437\u044b\u0432 \u043e\u0442\u043a\u043b\u043e\u043d\u0435\u043d')),
                ('anon', models.BooleanField(default=False, verbose_name='\u0410\u043d\u043e\u043d\u0438\u043c\u043d\u043e')),
                ('status', models.CharField(default=b'published', max_length=15, verbose_name='\u0421\u0442\u0430\u0442\u0443\u0441', choices=[(b'published', '\u041e\u043f\u0443\u0431\u043b\u0438\u043a\u043e\u0432\u0430\u043d\u043e'), (b'waiting', '\u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('content_type', models.ForeignKey(verbose_name='\u0422\u0438\u043f \u043e\u0431\u044a\u0435\u043a\u0442\u0430 \u043e\u0442\u0437\u044b\u0432\u0430', to='contenttypes.ContentType')),
                ('user', models.ForeignKey(verbose_name='\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '\u041e\u0442\u0437\u044b\u0432 \u043e \u043c\u043e\u0434\u0443\u043b\u0435',
                'verbose_name_plural': '\u041e\u0442\u0437\u044b\u0432\u044b \u043e \u043c\u043e\u0434\u0443\u043b\u0435',
            },
        ),
    ]
