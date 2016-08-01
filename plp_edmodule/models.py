# coding: utf-8

from django.core import validators
from django.db import models
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from plp.models import Course, Instructor, User
from plp_extension.apps.course_review.models import AbstractRating


class EducationalModule(models.Model):
    code = models.SlugField(verbose_name=_(u'Код'), unique=True)
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
    
    
class EducationalModuleEnrollment(models.Model):
    user = models.ForeignKey(User, verbose_name=_(u'Пользователь'))
    module = models.ForeignKey(EducationalModule, verbose_name=_(u'Образовательный модуль'))
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _(u'Запись на модуль')
        verbose_name_plural = _(u'Записи на модуль')
        unique_together = ('user', 'module')


class EducationalModuleProgress(models.Model):
    enrollment = models.OneToOneField(EducationalModuleEnrollment, verbose_name=_(u'Запись на модуль'),
                                      related_name='progress')
    progress = JSONField(verbose_name=_(u'Прогресс'), null=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_(u'Время последнего обращения к edx'))

    class Meta:
        verbose_name = _(u'Прогресс по модулю')
        verbose_name_plural = _(u'Прогресс по модулям')


class EducationalModuleUnsubscribe(models.Model):
    user = models.ForeignKey(User, verbose_name=_(u'Пользователь'))
    module = models.ForeignKey(EducationalModule, verbose_name=_(u'Образовательный модуль'))

    class Meta:
        verbose_name = _(u'Отписка от рассылок образовательного модуля')
        verbose_name_plural = _(u'Отписки от рассылок образовательного модуля')
        unique_together = ('user', 'module')


class EducationalModuleRating(AbstractRating):
    class Meta:
        verbose_name = _(u'Отзыв о модуле')
        verbose_name_plural = _(u'Отзывы о модуле')
