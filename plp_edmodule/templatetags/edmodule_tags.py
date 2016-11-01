# coding: utf-8

from django import template
from plp.models import Participant
from ..utils import course_set_attrs

register = template.Library()


@register.inclusion_tag('course/_enroll_button.html', takes_context=True)
def enroll_button(context, course, session=None):
    user = context['request'].user
    authenticated = user.is_authenticated()
    if not session:
        session = course.next_session
    status = session.button_status(user) if session else course.button_status(user)
    honor_accepted, enrolled = False, False
    if session and authenticated:
        p = Participant.objects.filter(session=session, user=user)
        if p:
            enrolled = True
            honor_accepted = p[0].honor_code_accepted
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
    }
