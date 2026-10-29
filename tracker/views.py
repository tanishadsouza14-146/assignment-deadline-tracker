from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import AssignmentForm, SubjectForm
from .models import Assignment, Subject


def _safe_next(request, default="tracker:dashboard"):
    """Redirect back to the page the user came from, but only if it is safe."""
    target = request.POST.get("next") or request.GET.get("next")
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}
    ):
        return redirect(target)
    return redirect(default)


# ------------------------------------------------------------- dashboard (READ)
def dashboard(request):
    today = timezone.localdate()
    soon = today + timedelta(days=getattr(settings, "DUE_SOON_DAYS", 3))
    not_done = ~Q(status=Assignment.COMPLETED)

    # Summary cards always reflect ALL assignments (not just the filtered ones).
    stats = Assignment.objects.aggregate(
        total=Count("id"),
        completed=Count("id", filter=Q(status=Assignment.COMPLETED)),
        overdue=Count("id", filter=Q(due_date__lt=today) & not_done),
        due_soon=Count(
            "id", filter=Q(due_date__gte=today, due_date__lte=soon) & not_done
        ),
    )
    stats["pending"] = stats["total"] - stats["completed"]
    stats["percent"] = (
        round(stats["completed"] * 100 / stats["total"]) if stats["total"] else 0
    )

    # ---- filters from the query string ----
    subject = request.GET.get("subject", "")
    status = request.GET.get("status", "")
    priority = request.GET.get("priority", "")
    query = request.GET.get("q", "").strip()

    assignments = Assignment.objects.select_related("subject").annotate(
        is_done=Case(
            When(status=Assignment.COMPLETED, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    )

    if subject.isdigit():
        assignments = assignments.filter(subject_id=int(subject))
    if status == "overdue":
        assignments = assignments.filter(due_date__lt=today).exclude(
            status=Assignment.COMPLETED
        )
    elif status == "due_soon":
        assignments = assignments.filter(
            due_date__gte=today, due_date__lte=soon
        ).exclude(status=Assignment.COMPLETED)
    elif status in dict(Assignment.STATUS_CHOICES):
        assignments = assignments.filter(status=status)
    if priority in dict(Assignment.PRIORITY_CHOICES):
        assignments = assignments.filter(priority=priority)
    if query:
        assignments = assignments.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    # Unfinished work first (earliest deadline on top), completed work last.
    assignments = assignments.order_by("is_done", "due_date")

    subject_summary = Subject.objects.annotate(
        total=Count("assignments"),
        pending=Count(
            "assignments", filter=~Q(assignments__status=Assignment.COMPLETED)
        ),
    ).filter(total__gt=0)

    context = {
        "assignments": assignments,
        "stats": stats,
        "subjects": Subject.objects.all(),
        "subject_summary": subject_summary,
        "status_choices": Assignment.STATUS_CHOICES,
        "priority_choices": Assignment.PRIORITY_CHOICES,
        "selected": {
            "subject": subject,
            "status": status,
            "priority": priority,
            "q": query,
        },
        "filters_active": any([subject, status, priority, query]),
        "result_count": assignments.count(),
    }
    return render(request, "tracker/dashboard.html", context)


# ------------------------------------------------------------------ CREATE
def assignment_create(request):
    if not Subject.objects.exists():
        messages.info(request, "Add a subject first, then you can create assignments.")
        return redirect("tracker:subjects")

    form = AssignmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        assignment = form.save()
        messages.success(request, f'Assignment "{assignment.title}" added.')
        return redirect("tracker:dashboard")
    return render(
        request,
        "tracker/assignment_form.html",
        {"form": form, "heading": "Add Assignment", "button": "Save Assignment"},
    )


# ------------------------------------------------------------------ UPDATE
def assignment_update(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    form = AssignmentForm(request.POST or None, instance=assignment)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f'Assignment "{assignment.title}" updated.')
        return redirect("tracker:dashboard")
    return render(
        request,
        "tracker/assignment_form.html",
        {"form": form, "heading": "Edit Assignment", "button": "Update Assignment"},
    )


@require_POST
def toggle_complete(request, pk):
    """Mark an assignment completed, or move it back to pending."""
    assignment = get_object_or_404(Assignment, pk=pk)
    if assignment.is_completed:
        assignment.status = Assignment.PENDING
        messages.info(request, f'"{assignment.title}" moved back to pending.')
    else:
        assignment.status = Assignment.COMPLETED
        messages.success(request, f'Nice! "{assignment.title}" marked as completed.')
    assignment.save()
    return _safe_next(request)


# ------------------------------------------------------------------ DELETE
def assignment_delete(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    if request.method == "POST":
        title = assignment.title
        assignment.delete()
        messages.success(request, f'Assignment "{title}" deleted.')
        return redirect("tracker:dashboard")
    return render(
        request, "tracker/assignment_confirm_delete.html", {"assignment": assignment}
    )


# ---------------------------------------------------------------- SUBJECTS
def subject_list(request):
    form = SubjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        subject = form.save()
        messages.success(request, f'Subject "{subject.name}" added.')
        return redirect("tracker:subjects")

    subjects = Subject.objects.annotate(total=Count("assignments"))
    return render(
        request, "tracker/subjects.html", {"form": form, "subjects": subjects}
    )


@require_POST
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    name = subject.name
    subject.delete()  # also removes that subject's assignments (CASCADE)
    messages.success(request, f'Subject "{name}" and its assignments were deleted.')
    return redirect("tracker:subjects")
