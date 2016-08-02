# coding: utf-8

from plp.notifications.base import MassSendEmails
from .models import EducationalModule, EducationalModuleEnrollment


class EdmoduleCourseStartsEmails(MassSendEmails):
    """
    Класс для массовой рассылки сообщений о начале курса, на который пользователь не записан,
    из образовательного модуля, на который он записан.
    """
    template_html = 'emails/edmodule_course_not_enrolled_starts_html.html'
    template_subject = 'emails/edmodule_course_not_enrolled_starts_subject.txt'

    def __init__(self, session):
        self.session = session
        super(EdmoduleCourseStartsEmails, self).__init__()
        self.email_to_username = {}

    def get_emails(self):
        enrollments = EducationalModuleEnrollment.objects.filter(
            module__in=EducationalModule.objects.filter(courses=self.session.course)
        )
        self.enrollment_by_email = dict([
            (i.user.email, i) for i in enrollments
        ])
        return list(set(self.enrollment_by_email.keys()))

    def get_context(self, email=None):
        return {
            'module': self.enrollment_by_email[email].module,
            'user': self.enrollment_by_email[email].user,
            'course': self.session.course,
            'site': self.get_site()
        }


class EdmoduleCourseEnrollEndsEmails(EdmoduleCourseStartsEmails):
    """
    Класс для массовой рассылки сообщений о конце записи на курс, на который пользователь не записан,
    из образовательного модуля, на который он записан.
    """
    template_html = 'emails/edmodule_course_enroll_ends_html.html'
    template_subject = 'emails/edmodule_course_enroll_ends_subject.txt'
