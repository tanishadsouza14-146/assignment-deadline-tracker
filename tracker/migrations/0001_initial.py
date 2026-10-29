import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Subject",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("code", models.CharField(blank=True, help_text="Optional course code, e.g. CS101", max_length=20)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Assignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=150)),
                ("description", models.TextField(blank=True)),
                ("due_date", models.DateField()),
                ("priority", models.CharField(choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")], default="medium", max_length=10)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("in_progress", "In Progress"), ("completed", "Completed")], default="pending", max_length=15)),
                ("completed_on", models.DateField(blank=True, editable=False, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("subject", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignments", to="tracker.subject")),
            ],
            options={"ordering": ["due_date", "-created_at"]},
        ),
    ]
