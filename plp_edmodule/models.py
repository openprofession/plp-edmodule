# coding: utf-8

from django.core import validators
from django.db import models
from django.utils.translation import ugettext_lazy as _
from plp.models import Course, Instructor


class EducationalModule(models.Model):
    courses = models.ManyToManyField(Course, verbose_name=_(u'Курсы'), related_name='education_modules')
    about = models.TextField(verbose_name=_(u'Описание'), blank=False)
    price = models.IntegerField(verbose_name=_(u'Стоимость'), blank=True, null=True)
    discount = models.IntegerField(verbose_name=_(u'Скидка'), blank=True, default=0, validators=[
        validators.MinValueValidator(0),
        validators.MaxValueValidator(100)
    ])

    class Meta:
        verbose_name = _(u'Образовательный модуль')
        verbose_name_plural = _(u'Образовательные модули')

    def __unicode__(self):
        return ', '.join(self.courses.values_list('slug', flat=True)) or self.about[:20]

    @property
    def duration(self):
        """
        сумма длительностей курсов (в неделях)
        """
        try:
            return sum([i.course_weeks() for i in self.courses.all()])
        except TypeError:
            return None

    @property
    def instructors(self):
        """
        объединение множества преподавателей всех курсов модуля
        """
        return Instructor.objects.filter(instructor_courses=self.courses.all()).distinct()

    # TODO: категории
