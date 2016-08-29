# coding: utf-8

from django.contrib import admin
from autocomplete_light import modelform_factory
from .models import EducationalModule, EducationalModuleEnrollment


class EducationalModuleAdmin(admin.ModelAdmin):
    pass


class EducationalModuleEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'module', 'is_active')
    form = modelform_factory(EducationalModuleEnrollment, exclude=[])


admin.site.register(EducationalModule, EducationalModuleAdmin)
admin.site.register(EducationalModuleEnrollment, EducationalModuleEnrollmentAdmin)
