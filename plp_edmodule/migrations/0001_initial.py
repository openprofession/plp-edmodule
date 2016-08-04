# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    replaces = [(b'plp_edmodule', '0001_initial'), (b'plp_edmodule', '0002_educationalmodule_code'), (b'plp_edmodule', '0003_educationalmoduleenrollment'), (b'plp_edmodule', '0004_educationalmoduleprogress'), (b'plp_edmodule', '0005_educationalmoduleunsubscribe'), (b'plp_edmodule', '0006_educationalmodulerating'), (b'plp_edmodule', '0007_module_enrollment_type_and_reason'), (b'plp_edmodule', '0008_educationalmodule_title'), (b'plp_edmodule', '0009_educationalmodule_cover')]

    dependencies = [
        ('plp', '0069_alt_fields_for_images'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EducationalModule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('about', models.TextField(verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435')),
                ('price', models.IntegerField(null=True, verbose_name='\u0421\u0442\u043e\u0438\u043c\u043e\u0441\u0442\u044c', blank=True)),
                ('discount', models.IntegerField(default=0, blank=True, verbose_name='\u0421\u043a\u0438\u0434\u043a\u0430', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('courses', models.ManyToManyField(related_name='education_modules', verbose_name='\u041a\u0443\u0440\u0441\u044b', to=b'plp.Course')),
                ('code', models.SlugField(default=None, unique=True, verbose_name='\u041a\u043e\u0434')),
            ],
            options={
                'verbose_name': '\u041e\u0431\u0440\u0430\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c\u043d\u044b\u0439 \u043c\u043e\u0434\u0443\u043b\u044c',
                'verbose_name_plural': '\u041e\u0431\u0440\u0430\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c\u043d\u044b\u0435 \u043c\u043e\u0434\u0443\u043b\u0438',
            },
        ),
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
        migrations.CreateModel(
            name='EducationalModuleUnsubscribe',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('module', models.ForeignKey(verbose_name='\u041e\u0431\u0440\u0430\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c\u043d\u044b\u0439 \u043c\u043e\u0434\u0443\u043b\u044c', to='plp_edmodule.EducationalModule')),
                ('user', models.ForeignKey(verbose_name='\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '\u041e\u0442\u043f\u0438\u0441\u043a\u0430 \u043e\u0442 \u0440\u0430\u0441\u0441\u044b\u043b\u043e\u043a \u043e\u0431\u0440\u0430\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c\u043d\u043e\u0433\u043e \u043c\u043e\u0434\u0443\u043b\u044f',
                'verbose_name_plural': '\u041e\u0442\u043f\u0438\u0441\u043a\u0438 \u043e\u0442 \u0440\u0430\u0441\u0441\u044b\u043b\u043e\u043a \u043e\u0431\u0440\u0430\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c\u043d\u043e\u0433\u043e \u043c\u043e\u0434\u0443\u043b\u044f',
            },
        ),
        migrations.AlterUniqueTogether(
            name='educationalmoduleunsubscribe',
            unique_together=set([('user', 'module')]),
        ),
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
        migrations.CreateModel(
            name='EducationalModuleEnrollmentReason',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('payment_type', models.CharField(default=None, max_length=16, null=True, verbose_name='\u0421\u043f\u043e\u0441\u043e\u0431 \u043f\u043b\u0430\u0442\u0435\u0436\u0430', choices=[(None, b''), (b'manual', b'manual'), (b'yamoney', b'yamoney'), (b'other', b'other')])),
                ('payment_order_id', models.CharField(help_text='\u041d\u043e\u043c\u0435\u0440 \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u0430 (\u0434\u043b\u044f \u044f\u043d\u0434\u0435\u043a\u0441-\u043a\u0430\u0441\u0441\u044b - \u043f\u043e\u043b\u0435 order_number)', max_length=64, null=True, verbose_name='\u041d\u043e\u043c\u0435\u0440 \u0434\u043e\u0433\u043e\u0432\u043e\u0440\u0430', blank=True)),
                ('payment_descriptions', models.TextField(help_text='\u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439 \u043a \u043f\u043b\u0430\u0442\u0435\u0436\u0443', null=True, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435 \u043f\u043b\u0430\u0442\u0435\u0436\u0430', blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('enrollment', models.ForeignKey(related_name='enrollment_reason', verbose_name='\u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0430 \u043c\u043e\u0434\u0443\u043b\u044c', to='plp_edmodule.EducationalModuleEnrollment')),
            ],
            options={
                'verbose_name': '\u041f\u0440\u0438\u0447\u0438\u043d\u0430 \u0437\u0430\u043f\u0438\u0441\u0438',
                'verbose_name_plural': '\u041f\u0440\u0438\u0447\u0438\u043d\u044b \u0437\u0430\u043f\u0438\u0441\u0438',
            },
        ),
        migrations.CreateModel(
            name='EducationalModuleEnrollmentType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True, verbose_name='\u0410\u043a\u0442\u0438\u0432\u0435\u043d')),
                ('mode', models.CharField(blank=True, help_text='course mode \u0432 edx', max_length=32, verbose_name='\u0422\u0438\u043f', choices=[(b'audit', b'audit'), (b'honor', b'honor'), (b'verified', b'verified')])),
                ('buy_start', models.DateTimeField(null=True, verbose_name='\u041d\u0430\u0447\u0430\u043b\u043e \u043f\u0440\u0438\u0435\u043c\u0430 \u043e\u043f\u043b\u0430\u0442\u044b', blank=True)),
                ('buy_expiration', models.DateField(null=True, verbose_name='\u041a\u0440\u0430\u0439\u043d\u044f\u044f \u0434\u0430\u0442\u0430 \u043e\u043f\u043b\u0430\u0442\u044b', blank=True)),
                ('price', models.PositiveIntegerField(default=0, verbose_name='\u0421\u0442\u043e\u0438\u043c\u043e\u0441\u0442\u044c')),
                ('about', models.TextField(verbose_name='\u041a\u0440\u0430\u0442\u043a\u043e\u0435 \u043e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', blank=True)),
                ('description', models.TextField(verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', blank=True)),
                ('module', models.ForeignKey(verbose_name='\u041e\u0431\u0440\u0430\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c\u043d\u044b\u0439 \u043c\u043e\u0434\u0443\u043b\u044c', to='plp_edmodule.EducationalModule')),
            ],
            options={
                'verbose_name': '\u0412\u0430\u0440\u0438\u0430\u043d\u0442 \u043f\u0440\u043e\u0445\u043e\u0436\u0434\u0435\u043d\u0438\u044f \u043c\u043e\u0434\u0443\u043b\u044f',
                'verbose_name_plural': '\u0412\u0430\u0440\u0438\u0430\u043d\u0442\u044b \u043f\u0440\u043e\u0445\u043e\u0436\u0434\u0435\u043d\u0438\u044f \u043c\u043e\u0434\u0443\u043b\u044f',
            },
        ),
        migrations.AddField(
            model_name='educationalmoduleenrollmentreason',
            name='module_enrollment_type',
            field=models.ForeignKey(verbose_name='\u0412\u0430\u0440\u0438\u0430\u043d\u0442 \u043f\u0440\u043e\u0445\u043e\u0436\u0434\u0435\u043d\u0438\u044f \u043c\u043e\u0434\u0443\u043b\u044f', to='plp_edmodule.EducationalModuleEnrollmentType'),
        ),
        migrations.AlterUniqueTogether(
            name='educationalmoduleenrollmenttype',
            unique_together=set([('module', 'mode')]),
        ),
        migrations.AddField(
            model_name='educationalmodule',
            name='title',
            field=models.CharField(default='', max_length=200, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='educationalmodule',
            name='cover',
            field=models.ImageField(upload_to=b'edmodule_cover', verbose_name='\u041e\u0431\u043b\u043e\u0436\u043a\u0430', blank=True),
        ),
    ]
