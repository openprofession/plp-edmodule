# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plp', '0073_merge'),
        ('plp_edmodule', '0011_auto_20170502_1443'),
    ]

    operations = [
        migrations.CreateModel(
            name='PromoCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=6, verbose_name='\u041f\u0440\u043e\u043c\u043e\u043a\u043e\u0434', blank=True)),
                ('product_type', models.CharField(default=b'course', max_length=10, verbose_name='\u0422\u0438\u043f \u043f\u0440\u043e\u0434\u0443\u043a\u0442\u0430', choices=[(b'course', '\u041a\u0443\u0440\u0441'), (b'edmodule', '\u0421\u043f\u0435\u0446\u0438\u0430\u043b\u0438\u0437\u0430\u0446\u0438\u044f')])),
                ('active_till', models.DateField(verbose_name='\u0410\u043a\u0442\u0443\u0430\u043b\u0435\u043d \u0434\u043e \u0434\u0430\u0442\u044b')),
                ('max_usage', models.PositiveSmallIntegerField(verbose_name='\u041a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e \u0432\u043e\u0437\u043c\u043e\u0436\u043d\u044b\u0445 \u043e\u043f\u043b\u0430\u0442')),
                ('used', models.PositiveSmallIntegerField(verbose_name='\u0411\u044b\u043b \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u043d')),
                ('use_with_others', models.BooleanField(default=True, verbose_name='\u041f\u0440\u0438\u043c\u0435\u043d\u044f\u0435\u0442\u0441\u044f \u0441 \u0434\u0440\u0443\u0433\u0438\u043c\u0438 \u0441\u043a\u0438\u0434\u043a\u0430\u043c\u0438')),
                ('discount_percent', models.DecimalField(null=True, verbose_name='\u041f\u0440\u043e\u0446\u0435\u043d\u0442 \u0441\u043a\u0438\u0434\u043a\u0438', max_digits=5, decimal_places=2, blank=True)),
                ('discount_price', models.DecimalField(null=True, verbose_name='\u041d\u043e\u0432\u0430\u044f \u0441\u0442\u043e\u0438\u043c\u043e\u0441\u0442\u044c \u043a\u0443\u0440\u0441\u0430', max_digits=8, decimal_places=2, blank=True)),
                ('course', models.ForeignKey(related_name='course', verbose_name='\u041a\u0443\u0440\u0441', blank=True, to='plp.Course', null=True)),
                ('edmodule', models.ForeignKey(related_name='edmodule', verbose_name='\u0421\u043f\u0435\u0446\u0438\u0430\u043b\u0438\u0437\u0430\u0446\u0438\u044f', blank=True, to='plp_edmodule.EducationalModule', null=True)),
            ],
            options={
                'verbose_name': '\u041f\u0440\u043e\u043c\u043e\u043a\u043e\u0434',
                'verbose_name_plural': '\u041f\u0440\u043e\u043c\u043e\u043a\u043e\u0434\u044b',
            },
        ),
    ]
