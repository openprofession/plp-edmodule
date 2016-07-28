# coding: utf-8

import logging
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import EducationalModule, EducationalModuleEnrollment
from .utils import update_module_enrollment_progress, client


@login_required
@require_POST
def edmodule_enroll(request):
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
