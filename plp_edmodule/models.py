# coding: utf-8

import random
from django.conf import settings
from django.core import validators
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from sortedm2m.fields import SortedManyToManyField
from plp.models import Course, User, SessionEnrollmentType, Participant
from plp_extension.apps.course_review.models import AbstractRating
from plp_extension.apps.course_review.signals import course_rating_updated_or_created, update_mean_ratings
from plp_extension.apps.module_extension.models import DEFAULT_COVER_SIZE
from plp_extension.apps.course_extension.models import CourseExtendedParameters
from .signals import edmodule_enrolled, edmodule_enrolled_handler, edmodule_payed, edmodule_payed_handler, \
    edmodule_unenrolled, edmodule_unenrolled_handler

HIDDEN = 'hidden'
PUBLISHED = 'published'


class EducationalModule(models.Model):
    STATUSES = (
        (HIDDEN, _(u'Скрыт')),
        (PUBLISHED, _(u'Опубликован')),
    )
    code = models.SlugField(verbose_name=_(u'Код'), unique=True)
    title = models.CharField(verbose_name=_(u'Название'), max_length=200)
    status = models.CharField(_(u'Статус'), max_length=16, choices=STATUSES, default='hidden')
    courses = SortedManyToManyField(Course, verbose_name=_(u'Курсы'), related_name='education_modules')
    cover = models.ImageField(_(u'Обложка EM'), upload_to='edmodule_cover', blank=True,
        help_text=_(u'Минимум {0}*{1}, картинки большего размера будут сжаты до этого размера').format(
            *getattr(settings, 'EDMODULE_COVER_IMAGE_SIZE', DEFAULT_COVER_SIZE)
    ))
    about = models.TextField(verbose_name=_(u'Описание'), blank=False)
    price = models.IntegerField(verbose_name=_(u'Стоимость'), blank=True, null=True)
    discount = models.IntegerField(verbose_name=_(u'Скидка'), blank=True, default=0, validators=[
        validators.MinValueValidator(0),
        validators.MaxValueValidator(100)
    ])
    sum_ratings = models.PositiveIntegerField(verbose_name=_(u'Сумма оценок'), default=0)
    count_ratings = models.PositiveIntegerField(verbose_name=_(u'Количество оценок'), default=0)

    class Meta:
        verbose_name = _(u'Образовательный модуль')
        verbose_name_plural = _(u'Образовательные модули')

    def __unicode__(self):
        return u'%s - %s' % (self.code, ', '.join(self.courses.values_list('slug', flat=True)))

    @cached_property
    def duration(self):
        """
        сумма длительностей курсов (в неделях)
        """
        duration = 0
        for c, s in self.courses_with_closest_sessions:
            d = s.get_duration() if s else c.duration
            if not d:
                return 0
            duration += d
        return duration

    @cached_property
    def whole_work(self):
        work = 0
        for c, s in self.courses_with_closest_sessions:
            if s:
                w = (s.get_duration() or 0) * (s.get_workload() or 0)
            else:
                w = (c.duration or 0) * (c.workload or 0)
            if not w:
                return 0
            work += w
        return work

    @property
    def workload(self):
        work = self.whole_work
        duration = self.duration
        if self.duration:
            return int(round(float(work) / duration, 0))
        return 0

    @property
    def instructors(self):
        """
        объединение множества преподавателей всех курсов модуля
        упорядочивание по частоте вхождения в сессии, на которые мы записываем пользователя
        """
        d = {}
        for c in self.courses.all():
            if c.next_session:
                for i in c.next_session.get_instructors():
                    d[i] = d.get(i, 0) + 1
            else:
                for i in c.instructor.all():
                    d[i] = d.get(i, 0) + 1
        result = sorted(d.items(), key=lambda x: x[1], reverse=True)
        return [i[0] for i in result]

    @property
    def categories(self):
        return self._get_sorted('categories')

    def get_authors(self):
        return self._get_sorted('authors')

    def get_partners(self):
        return self._get_sorted('partners')

    def get_authors_and_partners(self):
        result = []
        for i in self.get_authors() + self.get_partners():
            if not i in result:
                result.append(i)
        return result

    def _get_sorted(self, attr):
        d = {}
        for c in self.courses_extended.prefetch_related(attr):
            for item in getattr(c, attr).all():
                d[item] = d.get(item, 0) + 1
        result = sorted(d.items(), key=lambda x: x[1], reverse=True)
        return [i[0] for i in result]

    def get_schedule(self):
        """
        список тем
        """
        schedule = []
        all_courses = self.courses.values_list('id', flat=True)
        for c in self.courses_extended.prefetch_related('course'):
            if c.course.id not in all_courses:
                schedule.append({'course': {'title': c.course.title},
                                 'schedule': ''})
            else:
                schedule.append({'course': {'title': c.course.title},
                                 'schedule': c.themes})
        return schedule

    def get_rating(self):
        if self.count_ratings:
            return round(float(self.sum_ratings) / self.count_ratings, 2)
        return 0

    def get_related(self):
        """
        получение похожих курсов и специализаций (от 0 до 2)
        """
        from .utils import course_set_attrs
        categories = self.categories
        if not categories:
            return []
        modules = EducationalModule.objects.exclude(id=self.id).filter(
            courses__extended_params__categories__in=categories).distinct()
        courses = Course.objects.exclude(id__in=self.courses.values_list('id', flat=True)).filter(
            extended_params__categories__in=categories).distinct()
        if modules:
            return [{'type': 'em', 'item': random.sample(modules, 1)[0]},
                    {'type': 'course', 'item': course_set_attrs(random.sample(courses, 1)[0])}]
        elif courses:
            if len(courses) > 1:
                sample = [course_set_attrs(i) for i in random.sample(courses, 2)]
                return [{'type': 'course', 'item': sample[0]},
                        {'type': 'course', 'item': sample[1]}]
            return [{'type': 'course', 'item': course_set_attrs(courses[0])}]
        return []

    def get_sessions(self):
        """
        хелпер для выбора сессий
        """
        return [i.next_session for i in self.courses.all()]

    @cached_property
    def courses_extended(self):
        return CourseExtendedParameters.objects.filter(course__id__in=self.courses.values_list('id', flat=True))

    def get_module_profit(self):
        """ для блока "что я получу в итоге" """
        data = []
        for c in self.courses_extended:
            if c.profit:
                data.extend(c.profit.splitlines())
        data = [i.strip() for i in data if i.strip()]
        return list(set(data))

    def get_price_list(self):
        """
        :return: {
            'courses': [(курс(Course), цена(int), ...],
            'price': цена без скидок (int),
            'whole_price': цена со скидкой (float),
            'discount': скидка (int)
        }
        """
        types = dict([(i.session.id, i.price) for i in
                      SessionEnrollmentType.objects.filter(session__course__in=self.courses.all(), mode='verified')])
        result = {'courses': []}
        for c in self.courses.all():
            s = c.next_session
            if s:
                result['courses'].append((c, types.get(s.id)))
            else:
                result['courses'].append((c, None))
        try:
            price = sum([i[0] for i in result['courses']])
            whole_price = price * (1 - self.discount / 100.)
        except TypeError:
            price, whole_price = None, None
        result.update({
            'price': price,
            'whole_price': whole_price,
            'discount': self.discount
        })
        return result

    def get_start_date(self):
        c = self.courses.first()
        if c.next_session:
            return c.next_session.datetime_starts

    def course_status_params(self):
        from .utils import get_status_dict
        c = self.get_closest_course_with_session()
        if c:
            return get_status_dict(c[1])
        return {}

    @property
    def count_courses(self):
        return self.courses.count()

    @cached_property
    def courses_with_closest_sessions(self):
        from .utils import choose_closest_session
        courses = self.courses.exclude(extended_params__is_project=True)
        return [(c, choose_closest_session(c)) for c in courses]

    def get_closest_course_with_session(self):
        courses = self.courses_with_closest_sessions
        courses = filter(lambda x: x[1] and x[1].datetime_starts, courses)
        courses = sorted(courses, key=lambda x: x[1].datetime_starts)
        if courses:
            return courses[0]

    def may_enroll(self):
        courses = self.courses_with_closest_sessions
        return all(i[1] and i[1].allow_enrollments() for i in courses)

    def may_enroll_on_project(self, user):
        if not user.is_authenticated():
            return False
        if not EducationalModuleEnrollment.objects.filter(user=user, module=self, is_active=True).exists():
            return False
        courses = self.courses.filter(extended_params__is_project=False).values_list('id', flat=True)
        passed = {i: False for i in courses}
        participants = Participant.objects.filter(session__course__id__in=courses, user=user).values_list(
            'session__course__id', 'is_graduate')
        for course_id, is_graduate in participants:
            if is_graduate:
                passed[course_id] = True
        return all(i for i in passed.values())


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
course_rating_updated_or_created.connect(update_mean_ratings)
