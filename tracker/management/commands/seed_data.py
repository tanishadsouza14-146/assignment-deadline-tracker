from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from tracker.models import Assignment, Subject


class Command(BaseCommand):
    help = "Fill the database with sample subjects and assignments for demo/screenshots."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="Delete all existing subjects and assignments first.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            Assignment.objects.all().delete()
            Subject.objects.all().delete()

        today = timezone.localdate()
        subjects = {}
        for name, code in [
            ("Python Programming", "CS101"),
            ("Database Management Systems", "CS204"),
            ("Data Structures", "CS102"),
            ("Engineering Mathematics", "MA201"),
            ("Computer Networks", "CS305"),
        ]:
            subjects[name], _ = Subject.objects.get_or_create(
                name=name, defaults={"code": code}
            )

        P, I, C = Assignment.PENDING, Assignment.IN_PROGRESS, Assignment.COMPLETED
        H, M, L = Assignment.HIGH, Assignment.MEDIUM, Assignment.LOW

        samples = [
            # title, subject, offset_days, priority, status, description
            ("Django mini project report", "Python Programming", 2, H, I, "Student expense tracker report with screenshots and GitHub link."),
            ("Flask vs Django comparison", "Python Programming", 9, L, P, "One page comparison of both frameworks."),
            ("ER diagram for library system", "Database Management Systems", -2, H, P, "Draw ER diagram and convert to relational schema."),
            ("SQL joins practice sheet", "Database Management Systems", 5, M, P, "Solve all 20 queries from the practical sheet."),
            ("Linked list implementation", "Data Structures", 1, H, I, "Singly and doubly linked list with insert/delete."),
            ("Binary tree traversal lab", "Data Structures", -5, M, C, "Inorder, preorder and postorder in C++."),
            ("Laplace transform problem set", "Engineering Mathematics", 7, M, P, "Exercises 4.1 to 4.5."),
            ("Subnetting numericals", "Computer Networks", 0, M, P, "Solve the VLSM subnetting questions."),
            ("Wireshark packet analysis", "Computer Networks", 14, L, P, "Capture and analyse a TCP handshake."),
        ]

        created = 0
        for title, subject, offset, priority, status, desc in samples:
            _, was_created = Assignment.objects.get_or_create(
                title=title,
                subject=subjects[subject],
                defaults={
                    "due_date": today + timedelta(days=offset),
                    "priority": priority,
                    "status": status,
                    "description": desc,
                },
            )
            created += was_created

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(subjects)} subjects and {created} new assignments."
        ))
