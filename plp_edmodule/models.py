# coding: utf-8

from django.core import validators
from django.db import models
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from plp.models import Course, Instructor, User
from plp_extension.apps.course_review.models import AbstractRating
from .signals import edmodule_enrolled, edmodule_enrolled_handler, edmodule_payed, edmodule_payed_handler, \
    edmodule_unenrolled, edmodule_unenrolled_handler


class EducationalModule(models.Model):
    code = models.SlugField(verbose_name=_(u'Код'), unique=True)
    title = models.CharField(verbose_name=_(u'Название'), max_length=200)
    courses = models.ManyToManyField(Course, verbose_name=_(u'Курсы'), related_name='education_modules')
    cover = models.ImageField(_(u'Обложка'), upload_to='edmodule_cover', blank=True)
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
    is_paid = models.BooleanField(verbose_name=_(u'Прохождение оплачено'), default=False)
    is_graduated = models.BooleanField(verbose_name=_(u'Прохождение завершено'), default=False)
    is_active = models.BooleanField(default=False)
    _ctime = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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


class EducationalModuleEnrollmentType(models.Model):
    EDX_MODES = (
        ('audit', 'audit'),
        ('honor', 'honor'),
        ('verified', 'verified')
    )

    module = models.ForeignKey(EducationalModule, verbose_name=_(u'Образовательный модуль'))
    active = models.BooleanField(_(u'Активен'), default=True)
    mode = models.CharField(_(u'Тип'), max_length=32, choices=EDX_MODES, blank=True, help_text=_(u'course mode в edx'))
    buy_start = models.DateTimeField(_(u'Начало приема оплаты'), null=True, blank=True)
    buy_expiration = models.DateField(_(u'Крайняя дата оплаты'), null=True, blank=True)
    price = models.PositiveIntegerField(_(u'Стоимость'), default=0)
    about = models.TextField(_(u'Краткое описание'), blank=True)
    description = models.TextField(_(u'Описание'), blank=True)

    class Meta:
        verbose_name = _(u'Вариант прохождения модуля')
        verbose_name_plural = _(u'Варианты прохождения модуля')
        unique_together = (("module", "mode"),)


class EducationalModuleEnrollmentReason(models.Model):
    class PAYMENT_TYPE:
        MANUAL = 'manual'
        YAMONEY = 'yamoney'
        OTHER = 'other'
        CHOICES = [(v, v) for v in (MANUAL, YAMONEY, OTHER)]

    CHOICES = [(None, '')] + PAYMENT_TYPE.CHOICES
    enrollment = models.ForeignKey(EducationalModuleEnrollment, verbose_name=_(u'Запись на модуль'),
                                   related_name='enrollment_reason')
    module_enrollment_type = models.ForeignKey(EducationalModuleEnrollmentType,
                                               verbose_name=_(u'Вариант прохождения модуля'))
    payment_type = models.CharField(max_length=16, null=True, default=None, choices=CHOICES,
                                    verbose_name=_(u'Способ платежа'))
    payment_order_id = models.CharField(max_length=64, null=True, blank=True,
                                        help_text=_(u'Номер договора (для яндекс-кассы - поле order_number)'),
                                        verbose_name=_(u'Номер договора'))
    payment_descriptions = models.TextField(null=True, blank=True, help_text=_(u'Комментарий к платежу'),
                                            verbose_name=_(u'Описание платежа'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _(u'Причина записи')
        verbose_name_plural = _(u'Причины записи')


edmodule_enrolled.connect(edmodule_enrolled_handler, sender=EducationalModuleEnrollment)
edmodule_unenrolled.connect(edmodule_unenrolled_handler, sender=EducationalModuleEnrollment)
edmodule_payed.connect(edmodule_payed_handler, sender=EducationalModuleEnrollmentReason)
