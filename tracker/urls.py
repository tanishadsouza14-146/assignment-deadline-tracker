from django.urls import path

from . import views

app_name = "tracker"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("assignments/add/", views.assignment_create, name="assignment_add"),
    path("assignments/<int:pk>/edit/", views.assignment_update, name="assignment_edit"),
    path("assignments/<int:pk>/delete/", views.assignment_delete, name="assignment_delete"),
    path("assignments/<int:pk>/toggle/", views.toggle_complete, name="assignment_toggle"),
    path("subjects/", views.subject_list, name="subjects"),
    path("subjects/<int:pk>/delete/", views.subject_delete, name="subject_delete"),
]
