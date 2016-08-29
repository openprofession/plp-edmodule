# coding: utf-8

import random
import logging
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from plp.models import HonorCode, CourseSession, Course
from plp_extension.apps.course_extension.models import CourseExtendedParameters
from .models import EducationalModule, EducationalModuleEnrollment, PUBLISHED, HIDDEN
from .utils import update_module_enrollment_progress, client, get_feedback_list
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
        'courses': module.courses.all(),
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
        context.update({
            'authors': u', '.join([i.title for i in authors]),
            'partners': u', '.join([i.title for i in partners]),
            'authors_and_partners': authors + partners,
            'profits': [i.strip() for i in profits.splitlines() if i.strip()],
            'schedule': course_extended.themes,
            'related': related,
        })
    except CourseExtendedParameters.DoesNotExist:
        pass
