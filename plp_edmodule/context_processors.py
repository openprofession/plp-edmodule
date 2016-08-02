# coding: utf-8

from django.conf import settings


def data(request):
    return {
        'ENABLE_EDMODULE': getattr(settings, 'ENABLE_EDMODULE', False),
    }
