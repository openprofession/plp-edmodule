# coding: utf-8

from django import template
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from plp.models import Participant, EnrollmentReason, CourseSession
from plp.utils.rudate import STARTED, ENDED
from ..models import EducationalModuleEnrollmentReason, EducationalModuleEnrollment
from ..utils import course_set_attrs

register = template.Library()

try:
    course_session_content_type = ContentType.objects.get_for_model(CourseSession)
except RuntimeError:
    pass


@register.inclusion_tag('course/_enroll_button.html', takes_context=True)
def enroll_button(context, course, session=None, html_location=None):
    """
    отрисовка кнопки записи для курса
    """
    user = context['request'].user
    authenticated = user.is_authenticated()
    if not session:
        session = course.next_session
    status = session.button_status(user) if session else course.button_status(user)
    honor_accepted, enrolled = False, False
    has_module = getattr(course, 'has_module', False)
    if session and authenticated:
        p = Participant.objects.filter(session=session, user=user)
        if p:
            enrolled = True
            honor_accepted = p[0].honor_code_accepted
        enr_reason = EnrollmentReason.objects.filter(
            participant__user__id=user.id,
            participant__session__id=session.id,
            session_enrollment_type__mode='verified'
        )
        module_payment = EducationalModuleEnrollmentReason.objects.filter(
            enrollment__module__courses__id=session.course_id,
            enrollment__user__id=user.id,
            full_paid=True
        )
        has_paid = enr_reason.exists() or module_payment.exists()
        if not hasattr(course, 'has_module'):
            has_module = EducationalModuleEnrollment.objects.filter(
                user=user, is_active=True, module__courses__id=course.id).exists()
    else:
        has_paid = False
        has_module = False
    if getattr(settings, 'ENABLE_OPRO_PAYMENTS', False) and session:
        from opro_payments.models import UpsaleLink, ObjectEnrollment
        if not hasattr(session, 'upsales'):
            session.upsales = UpsaleLink.objects.filter(
                content_type=course_session_content_type,
                object_id=session.id,
                is_active=True
            )
        if not hasattr(session, 'bought_upsales') and authenticated:
            session.bought_upsales = ObjectEnrollment.objects.filter(
                user__id=user.id,
                upsale__in=session.upsales,
                is_active=True
            ).select_related('upsale')
    if session:
        materials_available = session.course_status()['code'] in [STARTED, ENDED] and session.access_allowed()
    else:
        materials_available = False
    return {
        'status': status,
        'session': session,
        'honor_required': session.honor_code_required if session else False,
        'honor_accepted': honor_accepted,
        'enrolled': enrolled,
        'authenticated': authenticated,
        'course_id': session.get_absolute_slug() if session else course.course_id(),
        'title': course.title,
        'request': context['request'],
        'course': course_set_attrs(course),
        'has_paid': has_paid,
        'has_module': has_module,
        'materials_available': materials_available,
        'html_location': html_location,
    }


@register.filter
def split_text(value, splitter=None):
    """
    разбивка value по splitter, дефолтно - по строкам
    """
    if not value:
        return []
    if splitter is None:
        return [i.strip() for i in value.splitlines() if i.strip()]
    return [i.strip() for i in value.split(splitter) if i.strip()]
