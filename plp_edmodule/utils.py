# coding: utf-8

import logging
import requests
from django.conf import settings
from django.utils import timezone
from raven import Client
from plp.utils.edx_enrollment import EDXEnrollment, EDXNotAvailable, EDXCommunicationError, EDXEnrollmentError
from plp.models import CourseSession
from .models import EducationalModuleProgress

RAVEN_CONFIG = getattr(settings, 'RAVEN_CONFIG', {})
client = None

if RAVEN_CONFIG:
    client = Client(RAVEN_CONFIG.get('dsn'))

REQUEST_TIMEOUT = 10


class EDXTimeoutError(EDXEnrollmentError):
    pass


class EDXEnrollmentExtension(EDXEnrollment):
    def request(self, path, method='GET', **kwargs):
        url = '%s%s' % (self.base_url, path)

        headers = kwargs.setdefault('headers', {})

        if self.access_token:
            headers["Authorization"] = "Bearer %s" % self.access_token
        else:
            headers["X-Edx-Api-Key"] = settings.EDX_API_KEY
        if method == 'POST':
            headers['Content-Type'] = 'application/json'

        kwargs_copy = kwargs.copy()
        kwargs_copy.pop('headers', None)
        error_data = {
            'path': path,
            'method': method,
            'data': kwargs_copy,
        }
        try:
            logging.debug("EDXEnrollment.request %s %s %s", method, url, kwargs)
            r = self.session.request(method=method, url=url, **kwargs)
        except requests.exceptions.Timeout:
            if client:
                client.captureMessage('EDX connection timeout', extra=error_data)
            logging.error('Edx connection timeout error: %s' % error_data)
            raise EDXTimeoutError('')
        except IOError as exc:
            error_data['exception'] = str(exc)
            if client:
                client.captureMessage('EDXNotAvailable', extra=error_data)
            logging.error('EDXNotAvailable error: %s' % error_data)
            raise EDXNotAvailable("Error: {}".format(exc))

        logging.debug("EDXEnrollment.request response=%s %s", r.status_code, r.content)

        error_data.update({'status_code': r.status_code, 'content': r.content})
        if 500 <= r.status_code:
            if client:
                client.captureMessage('EDXNotAvailable', extra=error_data)
            logging.error('EDXNotAvailable error: %s' % error_data)
            raise EDXNotAvailable("Invalid EDX http response: {} {}".format(r.status_code, r.content))

        if r.status_code != 200:
            if client:
                client.captureMessage('EDXCommunicationError', extra=error_data)
            logging.error('EDXCommunicationError error: %s' % error_data)
            raise EDXCommunicationError("Invalid EDX http response: {} {}".format(r.status_code, r.content))

        return r

    def get_courses_progress(self, user_id, course_ids, timeout=REQUEST_TIMEOUT):
        query = 'user_id={}&course_id={}'.format(
            user_id,
            ','.join(course_ids)
        )
        return self.request(
            method='GET',
            path='/api/extended/edmoduleprogress?{}'.format(query),
            timeout=timeout
        )


def update_module_enrollment_progress(enrollment):
    module = enrollment.module
    sessions = CourseSession.objects.filter(course__in=module.courses.all())
    course_ids = [s.get_absolute_slug_v1() for s in sessions if s.course_status().get('code') == 'started']
    try:
        data = EDXEnrollmentExtension().get_courses_progress(enrollment.user.username, course_ids).json()
        now = timezone.now().strftime('%H:%M:%S %Y-%m-%d')
        for k, v in data.iteritems():
            v['updated_at'] = now
        try:
            progress = EducationalModuleProgress.objects.get(enrollment=enrollment)
            p = progress.progress or {}
            p.update(data)
            progress.progress = p
            progress.save()
        except EducationalModuleProgress.DoesNotExist:
            EducationalModuleProgress.objects.create(enrollment=enrollment, progress=data)
    except EDXEnrollmentError:
        pass
