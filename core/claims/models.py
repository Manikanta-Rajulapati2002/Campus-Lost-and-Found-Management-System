from django.db import models
from django.conf import settings
from django.utils import timezone
from items.models import Item


class Claim(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('returned', 'Returned'),  # after physical return
    )

    # -------------------------
    # SYSTEM FIELDS
    # -------------------------

    created_by_system = models.BooleanField(default=False)  
    # True → system auto-created claim (User B found User A’s lost item)
    # False → user manually submitted claim form

    matched_lost_exists = models.BooleanField(default=False)

    # -------------------------
    # CLAIM LINKS
    # -------------------------

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='claims'
    )

    claimed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='claims_made'
    )

    # When lost item is matched to a found item
    matched_found_item = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matched_claims'
    )

    # -------------------------
    # USER INPUT FIELDS (Optional now)
    # -------------------------

    where_lost = models.CharField(max_length=255, null=True, blank=True)
    when_lost = models.DateField(null=True, blank=True)
    identifying_marks = models.TextField(null=True, blank=True)

    message = models.TextField(
        null=True,
        blank=True,
        help_text="Explain why you believe this item belongs to you. (Optional for system claims)"
    )

    # -------------------------
    # CLAIM STATE
    # -------------------------

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # -------------------------
    # ADMIN REVIEW FIELDS
    # -------------------------

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='claims_reviewed'
    )

    reviewed_at = models.DateTimeField(null=True, blank=True)
    decision_note = models.TextField(null=True, blank=True)

    # -------------------------
    # CLAIM ACTION LOGIC
    # -------------------------

    def mark_approved(self, reviewer, note=None):
        self.status = 'approved'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()

        if note:
            self.decision_note = note

        self.save()

        # Update lost item → returned
        self.item.status = 'returned'
        self.item.save()

        # Update found item → returned
        if self.matched_found_item:
            self.matched_found_item.status = 'returned'
            self.matched_found_item.save()

    def mark_rejected(self, reviewer, note=None):
        self.status = 'rejected'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()

        if note:
            self.decision_note = note

        self.save()

        # If rejected → found item goes back to unclaimed list
        if self.matched_found_item:
            self.matched_found_item.status = "unclaimed"
            self.matched_found_item.save()

    def __str__(self):
        return f"Claim #{self.id} on {self.item} by {self.claimed_by} [{self.status}]"
