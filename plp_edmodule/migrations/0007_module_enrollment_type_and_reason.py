# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plp_edmodule', '0006_educationalmodulerating'),
    ]

    operations = [
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
    ]
