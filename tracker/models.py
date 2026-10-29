from django.db import models
from django.utils import timezone


class Subject(models.Model):
    """A course / subject that assignments belong to (e.g. Python Programming)."""

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(
        max_length=20, blank=True, help_text="Optional course code, e.g. CS101"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}" if self.code else self.name


class Assignment(models.Model):
    """A single assignment with a deadline, priority and progress status."""

    # Status values
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (IN_PROGRESS, "In Progress"),
        (COMPLETED, "Completed"),
    ]

    # Priority values
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PRIORITY_CHOICES = [
        (LOW, "Low"),
        (MEDIUM, "Medium"),
        (HIGH, "High"),
    ]

    title = models.CharField(max_length=150)
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="assignments"
    )
    description = models.TextField(blank=True)
    due_date = models.DateField()
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default=MEDIUM
    )
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default=PENDING
    )
    completed_on = models.DateField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date", "-created_at"]

    def __str__(self):
        return f"{self.title} ({self.subject.name})"

    # ---- helpers used by views and templates ----
    @property
    def is_completed(self):
        return self.status == self.COMPLETED

    @property
    def is_overdue(self):
        return (not self.is_completed) and self.due_date < timezone.localdate()

    @property
    def days_left(self):
        """Days until the deadline (negative when overdue)."""
        return (self.due_date - timezone.localdate()).days

    @property
    def due_text(self):
        """Human friendly deadline text shown beside the date."""
        if self.is_completed:
            return "Completed"
        days = self.days_left
        if days < 0:
            n = abs(days)
            return f"{n} day{'s' if n != 1 else ''} overdue"
        if days == 0:
            return "Due today"
        if days == 1:
            return "Due tomorrow"
        return f"{days} days left"

    def save(self, *args, **kwargs):
        # Keep the completion date in sync with the status.
        if self.is_completed and self.completed_on is None:
            self.completed_on = timezone.localdate()
        elif not self.is_completed:
            self.completed_on = None
        super().save(*args, **kwargs)
