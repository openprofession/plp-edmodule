# coding: utf-8

from django.conf import settings
from django.dispatch import Signal
from django.template.loader import get_template
from emails.django import Message
from plp.utils.helpers import get_domain_url

edmodule_enrolled = Signal(providing_args=['instance'])
edmodule_unenrolled = Signal(providing_args=['instance'])
edmodule_payed = Signal(providing_args=['instance'])


def edmodule_enrolled_handler(**kwargs):
    instance = kwargs.get('instance')
    if instance:
        user = instance.user
        msg = Message(
            subject=get_template('emails/edmodule_enrolled_subject.txt'),
            html=get_template('emails/edmodule_enrolled_html.html'),
            mail_from=settings.EMAIL_NOTIFICATIONS_FROM,
            mail_to=(user.get_full_name(), user.email)
        )
        context = {'module': instance.module, 'user': user, 'site': get_domain_url()}
        msg.send(context={'context': context})


def edmodule_unenrolled_handler(**kwargs):
    """
    Отправка сообщения об успешной отписке от модуля
    instace - EducationalModuleEnrollment
    """
    instance = kwargs.get('instance')
    if instance:
        user = instance.user
        msg = Message(
            subject=get_template('emails/edmodule_unenrolled_subject.txt'),
            html=get_template('emails/edmodule_unenrolled_html.html'),
            mail_from=settings.EMAIL_NOTIFICATIONS_FROM,
            mail_to=(user.get_full_name(), user.email)
        )
        context = {'module': instance.module, 'user': user, 'site': get_domain_url()}
        msg.send(context={'context': context})


def edmodule_payed_handler(**kwargs):
    instance = kwargs.get('instance')
    if instance:
        module = instance.enrollment.module
        user = instance.enrollment.user
        msg = Message(
            subject=get_template('emails/edmodule_payed_subject.txt'),
            html=get_template('emails/edmodule_payed_html.html'),
            mail_from=settings.EMAIL_NOTIFICATIONS_FROM,
            mail_to=(user.get_full_name(), user.email)
        )
        context = {'module': module, 'user': user, 'site': get_domain_url()}
        msg.send(context={'context': context})
