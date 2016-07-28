# coding: utf-8

import logging
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.conf import settings
from raven import Client
from django.shortcuts import get_object_or_404
from .models import EducationalModule, EducationalModuleEnrollment

RAVEN_CONFIG = getattr(settings, 'RAVEN_CONFIG', {})
client = None

if RAVEN_CONFIG:
    client = Client(RAVEN_CONFIG.get('dsn'))


@login_required
@require_POST
def edmodule_enroll(request):
    ed_module_code = request.POST.get('ed_module_code', '')
    bad_ed_module_code = False
    if ed_module_code:
        try:
            edmodule = EducationalModule.objects.get(code=ed_module_code)
            try:
                enrollment = EducationalModuleEnrollment.objects.get(user=request.user, module=edmodule)
                if enrollment.is_active:
                    logging.info('User {} already enrolled in educational module {}'.format(
                        request.user.username, edmodule.code
                    ))
                    return JsonResponse({'status': 1})
                enrollment.is_active = True
                enrollment.save()
            except EducationalModuleEnrollment.DoesNotExist:
                EducationalModuleEnrollment.objects.create(
                    user=request.user, module=edmodule, is_active=True
                )
            logging.info('User {} successfully enrolled in educational module {}'.format(
                request.user.username, edmodule.code
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
