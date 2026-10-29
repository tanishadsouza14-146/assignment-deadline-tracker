from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import AssignmentForm
from .models import Assignment, Subject


def make_assignment(subject, days=3, **kwargs):
    data = dict(
        title="Sample assignment",
        subject=subject,
        due_date=timezone.localdate() + timedelta(days=days),
    )
    data.update(kwargs)
    return Assignment.objects.create(**data)


class ModelTests(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(name="Python")

    def test_overdue_detection(self):
        self.assertTrue(make_assignment(self.subject, days=-1).is_overdue)
        self.assertFalse(make_assignment(self.subject, days=1).is_overdue)

    def test_completed_is_never_overdue(self):
        a = make_assignment(self.subject, days=-4, status=Assignment.COMPLETED)
        self.assertFalse(a.is_overdue)

    def test_completed_on_is_set_and_cleared(self):
        a = make_assignment(self.subject)
        self.assertIsNone(a.completed_on)
        a.status = Assignment.COMPLETED
        a.save()
        self.assertEqual(a.completed_on, timezone.localdate())
        a.status = Assignment.PENDING
        a.save()
        self.assertIsNone(a.completed_on)

    def test_due_text(self):
        self.assertEqual(make_assignment(self.subject, days=0).due_text, "Due today")
        self.assertEqual(make_assignment(self.subject, days=1).due_text, "Due tomorrow")
        self.assertEqual(make_assignment(self.subject, days=5).due_text, "5 days left")
        self.assertEqual(make_assignment(self.subject, days=-2).due_text, "2 days overdue")


class FormTests(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(name="Python")

    def _data(self, **over):
        data = {
            "title": "Lab report",
            "subject": self.subject.pk,
            "description": "",
            "due_date": (timezone.localdate() + timedelta(days=2)).isoformat(),
            "priority": "medium",
            "status": "pending",
        }
        data.update(over)
        return data

    def test_valid_form(self):
        self.assertTrue(AssignmentForm(data=self._data()).is_valid())

    def test_past_due_date_rejected_for_new(self):
        past = (timezone.localdate() - timedelta(days=1)).isoformat()
        self.assertFalse(AssignmentForm(data=self._data(due_date=past)).is_valid())

    def test_past_due_date_allowed_when_editing(self):
        a = make_assignment(self.subject, days=-3)
        past = (timezone.localdate() - timedelta(days=1)).isoformat()
        form = AssignmentForm(data=self._data(due_date=past), instance=a)
        self.assertTrue(form.is_valid(), form.errors)

    def test_short_title_rejected(self):
        self.assertFalse(AssignmentForm(data=self._data(title="ab")).is_valid())


class ViewTests(TestCase):
    def setUp(self):
        self.py = Subject.objects.create(name="Python")
        self.db = Subject.objects.create(name="DBMS")

    def test_dashboard_loads_empty(self):
        resp = self.client.get(reverse("tracker:dashboard"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "No assignments yet")

    def test_dashboard_stats(self):
        make_assignment(self.py, days=-1, title="Late one")
        make_assignment(self.py, days=2, title="Soon one")
        make_assignment(self.db, days=10, title="Far one", status=Assignment.COMPLETED)
        resp = self.client.get(reverse("tracker:dashboard"))
        stats = resp.context["stats"]
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["completed"], 1)
        self.assertEqual(stats["pending"], 2)
        self.assertEqual(stats["overdue"], 1)
        self.assertEqual(stats["due_soon"], 1)
        self.assertEqual(stats["percent"], 33)

    def test_subject_filter(self):
        make_assignment(self.py, title="Python task")
        make_assignment(self.db, title="DBMS task")
        resp = self.client.get(reverse("tracker:dashboard"), {"subject": self.py.pk})
        self.assertContains(resp, "Python task")
        self.assertNotContains(resp, "DBMS task")

    def test_status_overdue_filter(self):
        make_assignment(self.py, days=-2, title="Late one")
        make_assignment(self.py, days=4, title="Fine one")
        resp = self.client.get(reverse("tracker:dashboard"), {"status": "overdue"})
        self.assertContains(resp, "Late one")
        self.assertNotContains(resp, "Fine one")

    def test_search(self):
        make_assignment(self.py, title="Django report")
        make_assignment(self.py, title="Flask notes")
        resp = self.client.get(reverse("tracker:dashboard"), {"q": "django"})
        self.assertContains(resp, "Django report")
        self.assertNotContains(resp, "Flask notes")

    def test_create_assignment(self):
        resp = self.client.post(reverse("tracker:assignment_add"), {
            "title": "New task",
            "subject": self.py.pk,
            "description": "",
            "due_date": (timezone.localdate() + timedelta(days=3)).isoformat(),
            "priority": "high",
            "status": "pending",
        })
        self.assertRedirects(resp, reverse("tracker:dashboard"))
        self.assertTrue(Assignment.objects.filter(title="New task").exists())

    def test_create_requires_a_subject(self):
        Subject.objects.all().delete()
        resp = self.client.get(reverse("tracker:assignment_add"))
        self.assertRedirects(resp, reverse("tracker:subjects"))

    def test_edit_assignment(self):
        a = make_assignment(self.py, title="Old title")
        resp = self.client.post(reverse("tracker:assignment_edit", args=[a.pk]), {
            "title": "New title",
            "subject": self.py.pk,
            "description": "",
            "due_date": a.due_date.isoformat(),
            "priority": "low",
            "status": "in_progress",
        })
        self.assertRedirects(resp, reverse("tracker:dashboard"))
        a.refresh_from_db()
        self.assertEqual(a.title, "New title")
        self.assertEqual(a.status, "in_progress")

    def test_toggle_complete(self):
        a = make_assignment(self.py)
        self.client.post(reverse("tracker:assignment_toggle", args=[a.pk]))
        a.refresh_from_db()
        self.assertTrue(a.is_completed)
        self.client.post(reverse("tracker:assignment_toggle", args=[a.pk]))
        a.refresh_from_db()
        self.assertFalse(a.is_completed)

    def test_toggle_rejects_get(self):
        a = make_assignment(self.py)
        resp = self.client.get(reverse("tracker:assignment_toggle", args=[a.pk]))
        self.assertEqual(resp.status_code, 405)

    def test_toggle_ignores_unsafe_next(self):
        a = make_assignment(self.py)
        resp = self.client.post(
            reverse("tracker:assignment_toggle", args=[a.pk]),
            {"next": "https://evil.example.com/"},
        )
        self.assertRedirects(resp, reverse("tracker:dashboard"))

    def test_delete_assignment(self):
        a = make_assignment(self.py)
        self.assertEqual(
            self.client.get(reverse("tracker:assignment_delete", args=[a.pk])).status_code, 200
        )
        self.client.post(reverse("tracker:assignment_delete", args=[a.pk]))
        self.assertFalse(Assignment.objects.filter(pk=a.pk).exists())

    def test_add_and_delete_subject(self):
        self.client.post(reverse("tracker:subjects"), {"name": "Maths", "code": "MA1"})
        self.assertTrue(Subject.objects.filter(name="Maths").exists())
        # duplicate (case-insensitive) is rejected
        self.client.post(reverse("tracker:subjects"), {"name": "maths", "code": ""})
        self.assertEqual(Subject.objects.filter(name__iexact="maths").count(), 1)
        s = Subject.objects.get(name="Maths")
        self.client.post(reverse("tracker:subject_delete", args=[s.pk]))
        self.assertFalse(Subject.objects.filter(pk=s.pk).exists())
