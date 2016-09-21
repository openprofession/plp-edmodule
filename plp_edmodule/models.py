# coding: utf-8

import random
from collections import defaultdict, OrderedDict
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core import validators
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from sortedm2m.fields import SortedManyToManyField
from plp.models import Course, User, SessionEnrollmentType, Participant
from plp_extension.apps.course_review.models import AbstractRating
from plp_extension.apps.course_review.signals import course_rating_updated_or_created, update_mean_ratings
from plp_extension.apps.module_extension.models import DEFAULT_COVER_SIZE, EducationalModuleExtendedParameters
from plp_extension.apps.course_extension.models import CourseExtendedParameters
from .signals import edmodule_enrolled, edmodule_enrolled_handler, edmodule_payed, edmodule_payed_handler, \
    edmodule_unenrolled, edmodule_unenrolled_handler
from plp_eduplanner import models as edu_models

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

    def __init__(self, *args, **kwargs):
        super(EducationalModule, self).__init__(*args, **kwargs)
        try:
            ext = self.extended_params
        except EducationalModuleExtendedParameters.DoesNotExist:
            ext = None
        for field in EducationalModuleExtendedParameters._meta.fields:
            if not field.auto_created and field.editable:
                setattr(self, field.name, getattr(ext, field.name) if ext else None)

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
        for c in self.get_courses():
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
        related = []
        if modules:
            related.append({'type': 'em', 'item': random.sample(modules, 1)[0]})
        if courses:
            sample = [course_set_attrs(i) for i in random.sample(courses, min(len(courses), 2))]
            for i in range(2 - len(related)):
                try:
                    related.append({'type': 'course', 'item': sample[i]})
                except IndexError:
                    pass
        return related

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
        for c in self.get_courses():
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
        c = self.get_courses()
        if not c:
            return None
        c = c[0]
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
        return len(self.get_courses())

    @cached_property
    def courses_with_closest_sessions(self):
        return [(c, c.next_session) for c in self.get_courses()]

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

    @property
    def review_count(self):
        return EducationalModuleRating.objects.filter(object_id=self.id).count()

    def get_courses(self):
        return self._all_courses

    @cached_property
    def _all_courses(self):
        from .utils import course_set_attrs
        return [course_set_attrs(i) for i in self.courses.all()]

    @cached_property
    def related_professions(self):
        """
        Получение профессий, соответствующих образовательному модулю
        Метод отбора: для каждой профессии выбирается список ее курсов, который бы увидел
        неавторизованный пользователь (или просто без компетенций), если ВСЕ курсы модуля
        содержатся в этом списке, то такая профессия соответствует модулю
        """
        user = AnonymousUser()
        related = edu_models.ProfessionComp.objects.filter(profession__is_public=True, comp__is_public=True).\
            select_related('comp__parent', 'profession__id')
        related_dict = defaultdict(list)
        for i in related:
            related_dict[i.profession.id].append(i)
        prof_comps_dict, required_dict, required_set_dict = {}, {}, {}
        user_comps = {}
        for k, v in related_dict.iteritems():
            prof_comps = {x.comp_id: x.rate for x in v}
            tmp = edu_models.Competence.get_required_comps(prof_comps, user_comps)
            required_dict[k] = tmp
            required_set_dict[k] = set(tmp.keys())
        qs = Course.objects.filter(status=PUBLISHED, competencies__isnull=False).prefetch_related('competencies')
        # т.к. нет приоритезации для курсов с одинаковыми компетенциями, придерживаемся того порядка курсов,
        # который используется при построении учебного плана на странице профессии
        course_dict = OrderedDict([(course, [i.comp_id for i in course.competencies.all()]) for course in qs])
        expected_courses_dict = {}
        for prof_id, comps in required_dict.iteritems():
            courses = [c for c, ids in course_dict.iteritems() if set(ids).intersection(set(comps))]
            courses = sorted(courses,
                key=lambda x: len(required_set_dict[prof_id] - set([x.comp_id for x in x.competencies.all()])))
            expected_courses_dict[prof_id] = courses
        prof_courses = {}
        for i in expected_courses_dict.keys():
            prof_courses[i] = [c for c, __ in
                               edu_models.Competence.get_plan(expected_courses_dict[i], required_dict[i].copy(), user)]
        module_courses = set([i.id for i in self.courses.all()])
        professions = [prof for prof, courses in prof_courses.iteritems()
                       if module_courses.issubset(set([i.id for i in courses]))]
        return edu_models.Profession.objects.filter(id__in=professions)

    def get_requirements(self):
        val = getattr(self, 'requirements', None)
        return [i.strip() for i in val.splitlines() if i.strip()] if val else []

    def get_profit(self):
        val = getattr(self, 'profit', None)
        return [i.strip() for i in val.splitlines() if i.strip()] if val else []

    def get_documents(self):
        val = getattr(self, 'documents', None)
        return [i.strip() for i in val.splitlines() if i.strip()] if val else []

    def get_competencies(self):
        """
        Компетенции образовательного модуля
        :returns список словарей вида {
            title: строка,
            children: массив строк,
            percent: число [0, 100]
            root_title: строка (название компетенции верхнего уровня)
        }
        """
        comps = edu_models.CourseComp.objects.filter(course__id__in=[i.id for i in self.courses.all()]).\
            select_related('comp', 'comp__parent__parent__title').distinct()
        children = defaultdict(list)
        root_name = {}
        for i in comps.filter(comp__level=2):
            children[i.comp.parent_id].append(i.comp)
            root_name[i.comp.parent_id] = i.comp.parent.parent.title
        result = []
        for item in edu_models.Competence.objects.filter(id__in=children.keys()).annotate(
                children_count=models.Count('children')):
            ch = [child.title for child in children.get(item.id, [])]
            result.append({
                'title': item.title,
                'children': ch,
                'percent': int(round(float(len(ch)) / item.children_count, 2) * 100),
                'root_title': root_name.get(item.id),
            })
        result = sorted(result, key=lambda x: x['root_title'])
        return result


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
