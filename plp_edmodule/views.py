# coding: utf-8

import logging
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from plp.models import HonorCode, CourseSession, Course
from .models import EducationalModule, EducationalModuleEnrollment, PUBLISHED, HIDDEN
from .utils import update_module_enrollment_progress, client
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
    return render(request, 'edmodule/edmodule_page.html', {
        'object': module,
        'courses': module.courses.all(),
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


def update_context_with_modules(context, user):
    if user.is_authenticated():
        modules = EducationalModule.objects.filter(educationalmoduleenrollment__user=user).distinct().order_by('title')
    else:
        modules = EducationalModule.objects.none()
    context['modules'] = modules


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
