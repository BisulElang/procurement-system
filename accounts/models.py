
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        REQUESTER = "REQUESTER", "Requester"
        APPROVER = "APPROVER", "Approver"
        PROCUREMENT_OFFICER = (
            "PROCUREMENT_OFFICER",
            "Procurement Officer",
        )
        PROCUREMENT_MANAGER = (
            "PROCUREMENT_MANAGER",
            "Procurement Manager",
        )

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.REQUESTER,
    )

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"
