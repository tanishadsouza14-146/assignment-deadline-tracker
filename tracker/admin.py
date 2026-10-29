from django.contrib import admin

from .models import Assignment, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "due_date", "priority", "status")
    list_filter = ("status", "priority", "subject")
    search_fields = ("title", "description")
    date_hierarchy = "due_date"
