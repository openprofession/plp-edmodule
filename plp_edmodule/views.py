# coding: utf-8

import os
import json
import random
import logging
from collections import defaultdict
from django.conf import settings
from django.db.models import Count
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.html import strip_tags, strip_spaces_between_tags
from django.utils.text import Truncator
from django.views.decorators.cache import cache_page
from plp.models import HonorCode, CourseSession, Course, Participant, EnrollmentReason, SessionEnrollmentType
from plp.utils.edx_enrollment import EDXEnrollmentError
from plp.views.course import _enroll
from plp_extension.apps.course_extension.models import CourseExtendedParameters, Category
from .models import EducationalModule, EducationalModuleEnrollment, PUBLISHED, HIDDEN, EducationalModuleEnrollmentReason, \
    BenefitLink, CoursePromotion
from .utils import update_module_enrollment_progress, client, get_feedback_list, course_set_attrs, get_status_dict, \
    count_user_score, update_modules_graduation
from .signals import edmodule_enrolled


@login_required
@require_POST
def edmodule_enroll(request):
    """
    обработка подписки и отписки от образовательного модуля
    """
    ed_module_code = request.POST.get('ed_module_code', '')
    try:
        is_active = request.POST['is_active'] in ['true', 'True', True]
    except KeyError:
        is_active = True
    bad_ed_module_code = False
    if ed_module_code:
        try:
            edmodule = EducationalModule.objects.get(code=ed_module_code)
            try:
                enrollment = EducationalModuleEnrollment.objects.get(user=request.user, module=edmodule)
                if enrollment.is_active and is_active:
                    logging.info('User {} already enrolled in educational module {}'.format(
                        request.user.username, edmodule.code
                    ))
                    return JsonResponse({'status': 1})
                elif not enrollment.is_active and not is_active:
                    logging.info('User {} already unenrolled from educational module {}'.format(
                        request.user.username, edmodule.code
                    ))
                    return JsonResponse({'status': 1})
                enrollment.is_active = is_active
                enrollment.save()
                if is_active:
                    update_module_enrollment_progress(enrollment)
                    edmodule_enrolled.send(EducationalModuleEnrollment, instance=enrollment)
            except EducationalModuleEnrollment.DoesNotExist:
                if not is_active:
                    if client:
                        client.captureMessage('User without active enrollment tried to unenroll from module',
                                              extra={'user': request.user.username, 'module': edmodule.code})
                    logging.error('User {} without active enrollment tried to unenroll from module {}'.format(
                        request.user.username, edmodule.code
                    ))
                    return JsonResponse({'status': 1})
                enr = EducationalModuleEnrollment.objects.create(
                    user=request.user, module=edmodule, is_active=is_active
                )
                update_module_enrollment_progress(enr)
                edmodule_enrolled.send(EducationalModuleEnrollment, instance=enr)
            logging.info('User {} successfully {} educational module {}'.format(
                request.user.username, 'enrolled in' if is_active else 'unenrolled from', edmodule.code
            ))
            return JsonResponse({'status': 0})
        except EducationalModule.DoesNotExist:
            bad_ed_module_code = True
    else:
        bad_ed_module_code = True
    if bad_ed_module_code:
        if client:
            client.captureMessage('Invalid module code', extra={
                'user': request.user.username,
                'ed_module_code': ed_module_code,
            })
        logging.error('Educational module "{}" not found'.format(ed_module_code))
    return JsonResponse({'status': 1})


def module_page(request, code):
    """
    страница образовательного модуля
    """
    module = get_object_or_404(EducationalModule, code=code)
    if module.status == HIDDEN and not request.user.is_staff:
        raise Http404
    authors = module.get_authors()
    partners = module.get_partners()
    # TODO: catalog_link
    # catalog_link = reverse('modules_catalog') + '?' + '&'.join(['cat=%s' % i.code for i in module.categories])
    catalog_link = ''
    upsale_links = []
    if getattr(settings, 'ENABLE_OPRO_PAYMENTS', False):
        from opro_payments.models import UpsaleLink
        upsale_links = UpsaleLink.objects.filter(
            object_id=module.id,
            content_type=ContentType.objects.get_for_model(module),
            is_active=True,
        ).select_related('upsale')
    try:
        session, price = module.get_first_session_to_buy(request.user)
    except TypeError:
        session, price = None, None
    return render(request, 'edmodule/edmodule_page.html', {
        'object': module,
        'courses': [course_set_attrs(i) for i in module.courses.all()],
        'authors': u', '.join([i.title for i in authors]),
        'partners': u', '.join([i.title for i in partners]),
        'authors_and_partners': module.get_authors_and_partners(),
        'profits': module.get_module_profit(),
        'related': module.get_related(),
        'price_data': module.get_price_list(request.user),
        'schedule': module.get_schedule(),
        'rating': module.get_rating(),
        'count_ratings': module.count_ratings,
        'catalog_link': catalog_link,
        'start_date': module.get_start_date(),
        'feedback_list': get_feedback_list(module),
        'instructors': module.instructors,
        'authenticated': request.user.is_authenticated(),
        'upsale_links': upsale_links,
        'enrollment_reason': module.get_enrollment_reason_for_user(request.user),
        'first_session': session,
        'first_session_price': price,
        'benefit_links': BenefitLink.get_benefits_for_object(module),
    })


@require_POST
@login_required
def get_honor_text(request):
    course_id = request.POST.get('course_id')
    split = course_id.split('/')
    honor_text = ''
    if len(split) == 3:
        session = get_object_or_404(CourseSession,
                                    course__university__slug=split[0],
                                    course__slug=split[1],
                                    slug=split[2])
        honor_text = HonorCode.objects.get_text_for_session(session)
    return JsonResponse({'honor_text': honor_text})


def update_context_with_modules(context, user):
    """
    Добавление в контекст модулей с доступными для записи сессиями и информацией по записи пользователя на них,
    покупки сессий и доступности платных/бесплатных вариантов прохождения, добавление апсейлов
    и информации об их покупке для всех сессий в контексте
    """
    def _remove_duplicates(s, lists):
        for item in lists:
            try:
                item.remove(s)
            except ValueError:
                pass

    def _assign_module_tab(module, session, course):
        if session in current:
            module.courses_current.append((course, session))
        if session in finished:
            module.courses_finished.append((course, session))
        if session in future:
            module.courses_feature.append((course, session))

    if user.is_authenticated():
        modules = EducationalModule.objects.filter(educationalmoduleenrollment__user=user).distinct().order_by('title')
        enrollment_reasons = EducationalModuleEnrollmentReason.objects.filter(enrollment__user=user).\
            order_by('-full_paid').select_related('enrollment__module__id')
        reason_for_module = {}
        for e in enrollment_reasons:
            if e.enrollment.module.id in reason_for_module:
                continue
            reason_for_module[e.enrollment.module.id] = e
        for m in modules:
            m.enrollment_reason = reason_for_module.get(m.id)
            price_data = m.get_price_list(user)
            price_data.pop('courses', None)
            m.price_data = json.dumps(price_data)
    else:
        modules = EducationalModule.objects.none()
    context['modules'] = modules
    current = context['courses_current']
    finished = context['courses_finished']
    future = context['courses_feature']
    upsales_for_session = defaultdict(list)
    upsales_for_module = defaultdict(list)
    obj_enrollments_for_session = defaultdict(list)
    obj_enrollments_for_module = defaultdict(list)
    modules_courses_ids = list(modules.values_list('courses__course_sessions__id', flat=True))
    modules_courses_ids = filter(lambda x: x, modules_courses_ids)
    if getattr(settings, 'ENABLE_OPRO_PAYMENTS', False):
        from opro_payments.models import UpsaleLink, ObjectEnrollment
        course_ids = [i.id for i in (finished + future + current)]
        course_ids = list(set(course_ids).union(set(modules_courses_ids)))
        ctype = ContentType.objects.get_for_model(CourseSession)
        ctype_module = ContentType.objects.get_for_model(EducationalModule)
        upsale_links = UpsaleLink.objects.filter(content_type=ctype, object_id__in=course_ids, is_active=True)
        module_upsale_links = UpsaleLink.objects.filter(content_type=ctype_module,
                                                        object_id__in=[i.id for i in modules], is_active=True)
        for i in upsale_links:
            upsales_for_session[i.object_id].append(i)
        for i in module_upsale_links:
            upsales_for_module[i.object_id].append(i)
        obj_enrollments = ObjectEnrollment.objects.filter(upsale__in=upsale_links, user=user).select_related('upsale')
        module_obj_enrollments = ObjectEnrollment.objects.filter(upsale__in=module_upsale_links, user=user).select_related('upsale')
        for i in obj_enrollments:
            obj_enrollments_for_session[i.upsale.object_id].append(i.upsale)
        for i in module_obj_enrollments:
            obj_enrollments_for_module[i.upsale.object_id].append(i.upsale)
    for i in (current + future + finished):
        i.upsales = upsales_for_session.get(i.id)
        i.bought_upsales = obj_enrollments_for_session.get(i.id)
    sessions_for_course = defaultdict(list)
    available_sessions_for_course = defaultdict(list)
    for cs in CourseSession.objects.filter(id__in=modules_courses_ids).order_by('datetime_starts'):
        sessions_for_course[cs.course_id].append(cs)
        if cs.allow_enrollments():
            available_sessions_for_course[cs.course_id].append(cs)
    participant_for_session = {i.session_id: i for i in
                               Participant.objects.filter(user=user, session__id__in=modules_courses_ids)}
    paid_enrollment_for_session = {i.participant.session.id: i for i in
                                   EnrollmentReason.objects.filter(
                                       participant__in=participant_for_session.values(),
                                       session_enrollment_type__mode='verified').select_related('participant__session__id')}
    honor_mode_for_session = {i.session_id: i for i in
                              SessionEnrollmentType.objects.filter(session__id__in=modules_courses_ids, mode__in=['honor'])}
    verified_mode_for_session = {i.session_id: i for i in
                              SessionEnrollmentType.objects.filter(session__id__in=modules_courses_ids, mode__in=['verified'])}
    without_duplicates = {
        'courses_current': current[:],
        'courses_finished': finished[:],
        'courses_feature': future[:]
    }
    update_modules_graduation(user, context['courses_finished'])
    for module in context['modules']:
        all_courses = module.courses.all()
        module.all_courses = zip(all_courses, [c.next_session for c in all_courses])
        module.upsales = upsales_for_module.get(module.id, [])
        module.bought_upsales = obj_enrollments_for_module.get(module.id, [])
        for attr in ['courses_current', 'courses_finished', 'courses_feature']:
            setattr(module, attr, [])
        for index, (course, __) in enumerate(module.all_courses, 1):
            course.available_sessions = available_sessions_for_course[course.id]
            course.index = index
            course.has_module = True
            for session in sessions_for_course[course.id]:
                session.participant = participant_for_session.get(session.id)
                session.paid_enrollment = paid_enrollment_for_session.get(session.id)
                session.verified_mode_enrollment_type = verified_mode_for_session.get(session.id)
                session.honor_mode_enrollment_type = honor_mode_for_session.get(session.id)
                if session.verified_mode_enrollment_type:
                    session.has_honor_mode = bool(session.honor_mode_enrollment_type)
                else:
                    session.has_honor_mode = True
                session.upsales = upsales_for_session.get(session.id)
                session.bought_upsales = obj_enrollments_for_session.get(session.id)
                if session.participant:
                    _assign_module_tab(module, session, course)
                    _remove_duplicates(session, without_duplicates.values())
    context.update(without_duplicates)
    context['courses_all'] = reduce(lambda x, y: x + y, without_duplicates.values(), [])
    context['score'] = count_user_score(user)
    context['count_certificates'] = Participant.objects.filter(user=user, is_graduate=True).count()
    context['count_participant'] = Participant.objects.filter(user=user).count()
    counters = {}
    for attr in ['courses_all', 'courses_current', 'courses_finished', 'courses_feature']:
        counters[attr] = len(context[attr])
        counters[attr] += sum([len(m.all_courses if attr == 'courses_all' else getattr(m, attr)) for m in modules])
    context['counters'] = counters


def update_course_details_context(context, user):
    """
    в контекст страницы курса добавляются параметры:
    modules: специализации, в которые входит курс
    authors: строка, создатели курса
    partners: строка, партнеры курса курса
    authors_and_partners: массив объектов CourseCreator, у каждого есть поле image
    profits: массив строк "Результаты обучения"
    schedule: json вида [{"col1": "Неделя 1", "col2": "Текст"}, ...]
    related: массив <= 2 элементов вида {'type': 'em', 'item': item}, где
        type - 'em' или 'course', item обект специализации или курса

    также через object можно получать атрибуты связанного CourseExtendedParameters
    """
    modules = EducationalModule.objects.filter(courses=context['object']).distinct()
    context['modules'] = modules
    session = context['session']
    if session and getattr(settings, 'ENABLE_OPRO_PAYMENTS', False):
        from opro_payments.models import UpsaleLink
        ctype = ContentType.objects.get_for_model(session)
        upsale_links = UpsaleLink.objects.filter(content_type=ctype, object_id=session.id, is_active=True)\
            .select_related('upsale')
        context.update({'upsale_links': upsale_links})
    try:
        course_extended = context['object'].extended_params
        authors = list(course_extended.authors.all())
        partners = list(course_extended.partners.all())
        profits = course_extended.profit or ''
        categories = course_extended.categories.all()
        related = []
        if categories:
            modules = EducationalModule.objects.filter(
                courses__extended_params__categories__in=categories).distinct()
            courses = Course.objects.exclude(id=context['object'].id).filter(
                extended_params__categories__in=categories).distinct()
            if modules:
                related = [
                    {'type': 'em', 'item': random.sample(modules, 1)[0]},
                ]
            if courses:
                if len(courses) > 1 and len(related):
                    sample = [course_set_attrs(i) for i in random.sample(courses, 2)]
                    related = [
                        {'type': 'course', 'item': sample[0]},
                        {'type': 'course', 'item': sample[1]}
                    ]
                else:
                    related.append({'type': 'course', 'item': course_set_attrs(courses[0])})
        obj = course_set_attrs(context['object'])
        context.update({
            'object': obj,
            'authors': u', '.join([i.title for i in authors]),
            'partners': u', '.join([i.title for i in partners]),
            'authors_and_partners': authors + partners,
            'profits': [i.strip() for i in profits.splitlines() if i.strip()],
            'schedule': course_extended.themes,
            'related': related,
            'comps': obj.get_competencies(),
        })
    except CourseExtendedParameters.DoesNotExist:
        pass


def get_promoted_courses(limit=None):
    qs = CoursePromotion.objects.all()
    items = []
    for item in qs:
        if limit is not None and len(items) == limit:
            break
        obj = item.content_object
        if obj:
            item_type = 'em' if isinstance(obj, EducationalModule) else 'course'
            items.append({'type': item_type, 'item': obj})
    return items


def update_frontpage_context(context):
    CNT_COURSES = 5
    objects = get_promoted_courses(CNT_COURSES)
    objects_ids = []
    for item in objects:
        objects_ids.append((
            item['type'],
            item['item'].id
        ))
    now = timezone.now()
    course_ids = CourseSession.objects.filter(
        course__status=PUBLISHED,
        datetime_start_enroll__lt=now,
        datetime_end_enroll__gt=now
    ).values_list('course__id', flat=True).distinct()
    by_category, by_category_dpo = {}, {}
    for c in Category.objects.all():
        by_category[c.id] = list(CourseExtendedParameters.objects.filter(
            categories=c, is_dpo=False, course__id__in=course_ids).values_list('course__id', flat=True))
        by_category_dpo[c.id] = list(CourseExtendedParameters.objects.filter(
            categories=c, is_dpo=True, course__id__in=course_ids).values_list('course__id', flat=True))

    for c, ids in by_category.iteritems():
        if len(objects) >= CNT_COURSES:
            break
        modules = EducationalModule.objects.filter(
            status=PUBLISHED,
            courses__id__in=ids,
        ).prefetch_related('courses')
        added_module = False
        for m in modules:
            if m.may_enroll() and ('em', m.id) not in objects_ids:
                objects.append({'type': 'em', 'item': m})
                objects_ids.append(('em', m.id))
                added_module = True
                break
        if added_module:
            continue
        added = [i[1] for i in objects_ids if i[0] == 'course']
        c = Course.objects.filter(id__in=ids).exclude(id__in=added).first()
        if c and ('course', c.id) not in objects_ids:
            objects.append({'type': 'course', 'item': course_set_attrs(c)})
            objects_ids.append(('course', c.id))
    num_to_add = CNT_COURSES - len(objects)
    # добавляем рандомные курсы
    if num_to_add:
        added = [i[1] for i in objects_ids]
        for c in Course.objects.filter(status=PUBLISHED).exclude(id__in=added).order_by('?')[:num_to_add]:
            objects.append({'type': 'course', 'item': course_set_attrs(c)})


    objects_dpo, objects_dpo_ids = [], []
    for c, ids in by_category_dpo.iteritems():
        if len(objects_dpo) > CNT_COURSES:
            break
        modules = EducationalModule.objects.filter(
            status=PUBLISHED,
            courses__in=ids,
        ).prefetch_related('courses')
        added_module = False
        for m in modules:
            if m.may_enroll() and ('em', m.id) not in objects_dpo_ids:
                objects_dpo.append({'type': 'em', 'item': m})
                objects_dpo_ids.append(('em', m.id))
                added_module = True
                break
        if added_module:
            continue
        added = [i[1] for i in objects_dpo_ids if i[0] == 'course']
        c = Course.objects.filter(id__in=ids).exclude(id__in=added).first()
        if c and ('course', c.id) not in objects_dpo_ids:
            objects_dpo.append({'type': 'course', 'item': course_set_attrs(c)})
            objects_dpo_ids.append(('course', c.id))

    context.update({
        'objects': objects,
        'objects_dpo': objects_dpo,
    })


@require_GET
def edmodule_filter_view(request):
    """
    фильтрация курсов и образовательных модулей
    возвращает словарь с ключами
    courses: список списков [код курса, код вуза]
    modules: список кодов образовательных модулей
    """
    courses = Course.objects.filter(status=PUBLISHED)
    modules = EducationalModule.objects.filter(status=PUBLISHED)
    # допустимые для фильтрации значения и функции фильтрации
    filters = {
        'university_slug': lambda x, cs: cs.filter(university__slug__in=x)
    }
    for k in request.GET.keys():
        if k in filters:
            fn = filters[k]
            courses = fn(request.GET.getlist(k), courses)
    courses = courses.distinct()
    modules = modules.filter(courses__in=courses).distinct()
    result = {
        'courses': [[i.slug, i.university.slug] for i in courses],
        'modules': [i.code for i in modules]
    }
    return JsonResponse(result)


@cache_page(settings.PAGE_CACHE_TIME)
def edmodule_catalog_view(request, category=None):
    """
    Передаваемый контекст:
    chosen_category: None или slug выбранной категории
    categories: все существующие объекты Category, имеющие курсы
    courses: словарь, ключ - id курса, значение: {
        'title': строка,
        'authors': массив строк,
        'course_status_params': {
            'status': строка 'scheduled', 'started' или '',
            'date': опционально если status != '', дата окончания записи если status == 'started',
                дата начала курса если status == 'scheduled', строка вида дд.мм.гггг,
            'days_before_start': опционально если status == 'scheduled' число дней до начала курса
        }
    }
    modules: аналогично courses, значение: {
        'title',
        'authors',
        'course_status_params',
        'count_courses': число курсов в модуле
    }
    course_covers: словарь, ключ - id курса, значение - объект картинки курса
    module_covers: аналогично course_covers
    """
    def _choose_closest_session(c):
        sessions = c.course_sessions.all()
        if sessions:
            sessions = filter(lambda x: x.datetime_end_enroll and x.datetime_end_enroll > timezone.now()
                                    and x.datetime_starts, sessions)
            sessions = sorted(sessions, key=lambda x: x.datetime_end_enroll)
            if sessions:
                return sessions[0]
        return None

    courses, modules, course_covers, module_covers = {}, {}, {}, {}
    cover_path = Course._meta.get_field('cover').upload_to
    try:
        all_course_covers = default_storage.listdir(cover_path)[1]
    except OSError:
        all_course_covers = None
    cover_path = EducationalModule._meta.get_field('cover').upload_to
    try:
        all_module_covers = default_storage.listdir(cover_path)[1]
    except OSError:
        all_module_covers = None

    through_model = CourseExtendedParameters._meta.get_field('categories').rel.through
    category_for_course = defaultdict(list)
    category_slugs_with_having_courses = set()
    q = through_model.objects.values_list('courseextendedparameters__course__id', 'category__slug')
    for course, category in q:
        category_for_course[course].append(category)
        category_slugs_with_having_courses.add(category)

    courses_query = Course.objects.filter(status='published').prefetch_related(
        'extended_params', 'extended_params__authors', 'course_sessions').distinct()
    # if not category:
    #     courses_query = Course.objects.filter(status='published').prefetch_related(
    #         'extended_params', 'extended_params__authors', 'course_sessions').distinct()
    # else:
    #     courses_query = Course.objects.filter(status='published', extended_params__categories__slug=category).\
    #         prefetch_related('extended_params', 'extended_params__authors', 'course_sessions').distinct()
    for c in courses_query:
        if c.cover:
            cover_name = os.path.split(c.cover.name)[-1]
            if cover_name in all_course_covers:
                course_covers[c.pk] = c.cover
            else:
                if client:
                    client.captureMessage('Image not found: %s' % str(c.cover))
        dic = {
            'title': c.title,
            'course_status_params': '',
            'url': reverse('course_details', kwargs={'uni_slug': c.university.slug, 'slug': c.slug}),
        }
        c = course_set_attrs(c)
        max_length = CourseExtendedParameters._meta.get_field('short_description').max_length
        default_desc = strip_tags(strip_spaces_between_tags(c.description or ''))
        dic.update({
            'authors_and_partners': [{'url': i.link, 'title': i.abbr or i.title} for i in c.get_authors_and_partners()],
            'catalog_marker': getattr(c, 'catalog_marker', ''),
            'short_description': getattr(c, 'short_description', '') or Truncator(default_desc).chars(max_length),
            'categories': category_for_course.get(c.id, []),
        })
        session = _choose_closest_session(c)
        dic.update({'course_status_params': get_status_dict(session)})
        courses[c.id] = dic

    for m in EducationalModule.objects.filter(status='published', courses__id__in=courses.keys()).\
            annotate(cnt_courses=Count('courses')).select_related('extended_params'):
        if m.cover:
            cover_name = os.path.split(m.cover.name)[-1]
            if cover_name in all_module_covers:
                module_covers[m.pk] = m.cover
            else:
                if client:
                    client.captureMessage('Image not found: %s' % str(m.cover))

        try:
            extended = m.extended_params
        except:
            extended = None
        categories = reduce(lambda x, y: x + y, [category_for_course.get(i.id, []) for i in m.courses.all()], [])
        categories = list(set(categories))
        dic = {
            'title': m.title,
            'authors_and_partners': [{'url': i.link, 'title': i.abbr or i.title} for i in m.get_authors_and_partners()],
            'count_courses': m.cnt_courses,
            'short_description': extended and extended.short_description,
            'catalog_marker': extended and extended.catalog_marker,
            'categories': categories,
            'url': reverse('edmodule-page', kwargs={'code': m.code})
        }
        dic.update({'course_status_params': m.course_status_params()})
        modules[m.id] = dic

    context = {
        'chosen_category': category,
        'categories': Category.objects.filter(slug__in=category_slugs_with_having_courses),
        'courses': json.dumps(courses, ensure_ascii=False),
        'modules': json.dumps(modules, ensure_ascii=False),
        'course_covers': course_covers,
        'module_covers': module_covers,
    }
    return render(request, 'edmodule/catalog.html', context)


def enroll_on_course(session, request):
    def _add_verified_entry(participant, verified_type):
        try:
            EnrollmentReason.objects.create(
                participant=participant,
                session_enrollment_type=verified_type,
                payment_type=EnrollmentReason.PAYMENT_TYPE.OTHER,
                payment_descriptions='module',
            )
            return JsonResponse({'status': 1})
        except EDXEnrollmentError:
            return JsonResponse({'status': 0, 'error': 'edx error'})

    enrs = EducationalModuleEnrollment.objects.filter(user=request.user,
                                                      module__courses=session.course,
                                                      enrollment_reason__full_paid=True)
    verified = False
    # в предложении что тип записи на модуль всегда verified
    if enrs:
        verified = True
    participant = Participant.objects.filter(session=session, user=request.user).first()
    # проверяем что можно записаться
    if not verified and not session.allow_enrollments():
        return JsonResponse({'status': 0})
    elif verified and not participant and not session.allow_enrollments():
        return JsonResponse({'status': 0})
    elif not verified and not session.has_honor_mode():
        return JsonResponse({'status': 0})

    verified_type = session.get_verified_mode_enrollment_type()
    if verified and not verified_type:
        # если у сессии нет платного варианта прохождения
        verified = False

    if participant and verified:
        # если пользователь был записан на курс, стараемся добавить ему verified mode
        enr_reason = EnrollmentReason.objects.filter(participant=participant, session_enrollment_type=verified_type)
        if enr_reason:
            return JsonResponse({'status': 0, 'error': 'already enrolled in verified mode'})
        return _add_verified_entry(participant, verified_type)
    elif participant:
        return JsonResponse({'status': 0, 'error': 'already enrolled'})
    else:
        # если записи на курс не было
        try:
            _enroll(request=request, user=request.user, session=session)
        except EDXEnrollmentError:
            pass
        finally:
            if verified:
                # если надо записать в verified mode
                participant = Participant.objects.get(session=session, user=request.user)
                return _add_verified_entry(participant, verified_type)
            return JsonResponse({'status': 1})
