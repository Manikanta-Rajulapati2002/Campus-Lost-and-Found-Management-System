from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):

    ROLE_CHOICES = (
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('staff', 'Staff'),        # Non-teaching staff
        ('admin', 'Admin'),        # System admin
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

    # PERSON DETAILS
    date_of_birth = models.DateField(null=True, blank=True)

    # ADDRESS DETAILS
    address_line1 = models.CharField(max_length=255, null=True, blank=True)
    address_line2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    zip_code = models.CharField(max_length=20, null=True, blank=True)

    # ROLE-SPECIFIC FIELDS
    major = models.CharField(max_length=100, null=True, blank=True)           # For Students
    faculty_role = models.CharField(max_length=100, null=True, blank=True)    # For Faculty
    staff_role = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.message[:30]}"
