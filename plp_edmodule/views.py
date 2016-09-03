# coding: utf-8

import os
import json
import random
import logging
from django.db.models import Count
from django.core.files.storage import default_storage
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from plp.models import HonorCode, CourseSession, Course
from plp_extension.apps.course_extension.models import CourseExtendedParameters, Category
from .models import EducationalModule, EducationalModuleEnrollment, PUBLISHED, HIDDEN
from .utils import update_module_enrollment_progress, client, get_feedback_list, course_set_attrs, get_status_dict
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
    return render(request, 'edmodule/edmodule_page.html', {
        'object': module,
        'courses': [course_set_attrs(i) for i in module.courses.all()],
        'authors': u', '.join([i.title for i in authors]),
        'partners': u', '.join([i.title for i in partners]),
        'authors_and_partners': authors + partners,
        'profits': module.get_module_profit(),
        'related': module.get_related(),
        'price_data': module.get_price_list(),
        'schedule': module.get_schedule(),
        'rating': module.get_rating(),
        'count_ratings': module.count_ratings,
        'catalog_link': catalog_link,
        'start_date': module.get_start_date(),
        'feedback_list': get_feedback_list(module),
        'instructors': module.instructors,
        'authenticated': request.user.is_authenticated(),
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
                    sample = random.sample(courses, 2)
                    related = [
                        {'type': 'course', 'item': sample[0]},
                        {'type': 'course', 'item': sample[1]}
                    ]
                else:
                    related.append({'type': 'course', 'item': courses[0]})
        obj = course_set_attrs(context['object'])
        context.update({
            'object': obj,
            'authors': u', '.join([i.title for i in authors]),
            'partners': u', '.join([i.title for i in partners]),
            'authors_and_partners': authors + partners,
            'profits': [i.strip() for i in profits.splitlines() if i.strip()],
            'schedule': course_extended.themes,
            'related': related,
        })
    except CourseExtendedParameters.DoesNotExist:
        pass


def update_frontpage_context(context):
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

    objects = []
    for c, ids in by_category.iteritems():
        modules = EducationalModule.objects.filter(
            status=PUBLISHED,
            courses__id__in=ids,
        ).prefetch_related('courses')
        for m in modules:
            if m.may_enroll():
                objects.append({'type': 'em', 'item': m})
                continue
        courses = Course.objects.filter(id__in=ids)
        if courses:
            objects.append({'type': 'course', 'item': course_set_attrs(courses[0])})
        if len(objects) > 5:
            break

    objects_dpo = []
    for c, ids in by_category_dpo.iteritems():
        modules = EducationalModule.objects.filter(
            status=PUBLISHED,
            courses__in=ids,
        ).prefetch_related('courses')
        for m in modules:
            if m.may_enroll():
                objects_dpo.append({'type': 'em', 'item': m})
                continue
        courses = Course.objects.filter(id__in=ids)
        if courses:
            objects_dpo.append({'type': 'course', 'item': course_set_attrs(courses[0])})
        if len(objects_dpo) > 5:
            break

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


def edmodule_catalog_view(request, category=None):
    """
    Передаваемый контекст:
    chosen_category: None или slug выбранной категории
    categories: все существующие объекты Category
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
        try:
            extended = c.extended_params
            authors = [i.title for i in extended.authors.all()]
        except CourseExtendedParameters.DoesNotExist:
            authors = []
        dic = {
            'title': c.title,
            'authors': authors,
            'course_status_params': '',
        }
        session = _choose_closest_session(c)
        dic.update({'course_status_params': get_status_dict(session)})
        courses[c.id] = dic

    for m in EducationalModule.objects.filter(status='published', courses__id__in=courses.keys()).\
            annotate(cnt_courses=Count('courses')):
        if m.cover:
            cover_name = os.path.split(m.cover.name)[-1]
            if cover_name in all_module_covers:
                module_covers[m.pk] = m.cover
            else:
                if client:
                    client.captureMessage('Image not found: %s' % str(m.cover))

        dic = {
            'title': m.title,
            'authors': [i.title for i in m.get_authors()],
            'count_courses': m.cnt_courses,
        }
        dic.update({'course_status_params': m.course_status_params})

    context = {
        'chosen_category': category,
        'categories': Category.objects.all(),
        'courses': json.dumps(courses, ensure_ascii=False),
        'modules': json.dumps(modules, ensure_ascii=False),
        'course_covers': course_covers,
        'module_covers': module_covers,
    }
    return render(request, 'edmodule/catalog.html', context)
