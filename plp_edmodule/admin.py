# coding: utf-8

from django.contrib import admin
from .models import EducationalModule


class EducationalModuleAdmin(admin.ModelAdmin):
    filter_horizontal = ('courses', )

admin.site.register(EducationalModule, EducationalModuleAdmin)
