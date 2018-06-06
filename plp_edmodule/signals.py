# coding: utf-8

from django.conf import settings
from django.dispatch import Signal
from django.template.loader import get_template
from emails.django import Message
from plp.utils.helpers import get_domain_url, get_prefix_and_site

edmodule_enrolled = Signal(providing_args=['instance'])
edmodule_unenrolled = Signal(providing_args=['instance'])
edmodule_payed = Signal(providing_args=['instance'])


def edmodule_enrolled_handler(**kwargs):
    """
    Отправка сообщения об успешной записи на модуль
    instace - EducationalModuleEnrollment
    """
    instance = kwargs.get('instance')
    if instance:
        user = instance.user
        msg = Message(
            subject=get_template('emails/edmodule_enrolled_subject.txt'),
            html=get_template('emails/edmodule_enrolled_html.html'),
            mail_from=settings.EMAIL_NOTIFICATIONS_FROM,
            mail_to=(user.get_full_name(), user.email)
        )
        context = {'module': instance.module, 'user': user, 'site_url': get_domain_url()}
        context.update(get_prefix_and_site())
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
        context = {'module': instance.module, 'user': user, 'site_url': get_domain_url()}
        context.update(get_prefix_and_site())
        msg.send(context={'context': context})


def edmodule_payed_handler(**kwargs):
    """
    отправка сообщения об успешной оплате модуля
    instance - EducationalModuleEnrollmentReason
    """
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
        context = {
            'module': module,
            'user': user,
            'site_url': get_domain_url(),
            'promocodes': kwargs.get('promocodes', []),
            'shop_url': getattr(settings, 'PAYMENT_SHOP_URL', None),
        }
        context.update(get_prefix_and_site())
        msg.send(context={'context': context})
