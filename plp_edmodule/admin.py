# coding: utf-8

from django.contrib import admin
from django import forms
from django.utils.translation import ugettext_lazy as _
from autocomplete_light import modelform_factory
from statistics.admin import RemoveDeleteActionMixin
from plp_extension.apps.course_extension.models import CourseExtendedParameters
from plp_extension.apps.module_extension.admin import EducationalModuleExtendedInline
from .models import (
    EducationalModule,
    EducationalModuleEnrollment,
    EducationalModuleEnrollmentType,
    EducationalModuleEnrollmentReason,
)


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

    def clean_subtitle(self):
        val = self.cleaned_data.get('subtitle')
        if val and not (1 <= len([i for i in val.splitlines() if i.strip()]) <= 3):
            raise forms.ValidationError(_(u'Введите от 1 до 3 элементов, каждый с новой строки'))
        return val


class EducationalModuleAdmin(RemoveDeleteActionMixin, admin.ModelAdmin):
    form = EducationalModuleAdminForm
    inlines = [EducationalModuleExtendedInline]
    readonly_fields = ('sum_ratings', 'count_ratings')


class EducationalModuleEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'module', 'is_active')
    form = modelform_factory(EducationalModuleEnrollment, exclude=[])


class EducationalModuleEnrollmentReasonAdmin(admin.ModelAdmin):
    search_fields = ('enrollment__user__username', 'enrollment__user__email')
    list_display = ('enrollment', 'module_enrollment_type', )
    list_filter = ('enrollment__module__code', )


admin.site.register(EducationalModule, EducationalModuleAdmin)
admin.site.register(EducationalModuleEnrollment, EducationalModuleEnrollmentAdmin)
admin.site.register(EducationalModuleEnrollmentType)
admin.site.register(EducationalModuleEnrollmentReason, EducationalModuleEnrollmentReasonAdmin)
