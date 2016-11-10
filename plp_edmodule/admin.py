# coding: utf-8

from django.contrib import admin
from django import forms
from django.utils.translation import ugettext_lazy as _
from autocomplete_light import modelform_factory
from statistics.admin import RemoveDeleteActionMixin
from plp_extension.apps.course_extension.models import CourseExtendedParameters
from plp_extension.apps.module_extension.admin import EducationalModuleExtendedInline
from .models import EducationalModule, EducationalModuleEnrollment, EducationalModuleEnrollmentType


class EducationalModuleAdminForm(forms.ModelForm):
    class Meta:
        model = EducationalModule
        fields = '__all__'

    def clean_courses(self):
        courses = self.cleaned_data.get('courses')
        if courses:
            proj = CourseExtendedParameters.objects.filter(course__id__in=[i.id for i in courses], is_project=True)
            if proj:
                for p in proj:
                    if EducationalModule.objects.filter(courses=p.course).count() > 0:
                        raise forms.ValidationError(_(u'Проект {title} уже содержится в другом модуле').format(
                            title=p.course.title
                        ))
        return courses


class EducationalModuleAdmin(RemoveDeleteActionMixin, admin.ModelAdmin):
    form = EducationalModuleAdminForm
    inlines = [EducationalModuleExtendedInline]
    readonly_fields = ('sum_ratings', 'count_ratings')


class EducationalModuleEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'module', 'is_active')
    form = modelform_factory(EducationalModuleEnrollment, exclude=[])


admin.site.register(EducationalModule, EducationalModuleAdmin)
admin.site.register(EducationalModuleEnrollment, EducationalModuleEnrollmentAdmin)
admin.site.register(EducationalModuleEnrollmentType)
