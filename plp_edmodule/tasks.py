# coding: utf-8

from django.utils import timezone
from celery.schedules import crontab
from celery.task import periodic_task
from plp.models import CourseSession
from .notifications import EdmoduleCourseStartsEmails


@periodic_task(run_every=crontab(minute=0, hour=0))
def send_notification_module_course_starts():
    now = timezone.now()
    qs = CourseSession.objects.filter(datetime_starts__range=(
        timezone.make_aware(timezone.datetime.combine(now, timezone.datetime.min.time())),
        timezone.make_aware(timezone.datetime.combine(now, timezone.datetime.max.time()))
    ))
    for cs in qs:
        emails = EdmoduleCourseStartsEmails(cs)
        emails.send()
