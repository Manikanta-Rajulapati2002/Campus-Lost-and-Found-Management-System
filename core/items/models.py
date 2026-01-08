from django.db import models
from django.conf import settings

class Item(models.Model):
    ITEM_TYPE_CHOICES = (
        ('lost', 'Lost'),
        ('found', 'Found'),
    )

    STATUS_CHOICES = (
        ('unmatched','Unmatched'),
        ('matched','Matched'),
        ('claimed','Claimed'),
        ('unclaimed','Unclaimed'),
        ('returned','Returned'),
        ('disposed','Disposed'),
    )

    CATEGORY_CHOICES = [
        ("Electronics", "Electronics"),
        ("Clothing", "Clothing"),
        ("Accessories", "Accessories"),
        ("Bags", "Bags"),
        ("Books", "Books"),
        ("Documents", "Documents"),
        ("Money", "Money"),
        ("Living Things", "Living Things"),   # NEW CATEGORY
        ("Other", "Other"),
    ]

    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='items_reported'
    )

    item_name = models.CharField(max_length=100)
    description = models.TextField()

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    color = models.CharField(max_length=30, blank=True)
    location = models.CharField(max_length=100)

    item_type = models.CharField(
        max_length=10,
        choices=ITEM_TYPE_CHOICES
    )

    # --- DATE & TIME CHANGES ---
    # For LOST items:
    date_lost = models.DateField(null=True, blank=True)
    time_lost_exact = models.TimeField(null=True, blank=True)
    time_lost_from = models.TimeField(null=True, blank=True)
    time_lost_to = models.TimeField(null=True, blank=True)

    # For FOUND items:
    date_found = models.DateField(null=True, blank=True)
    time_found = models.TimeField(null=True, blank=True)

    # --- Meta Info ---
    date_reported = models.DateField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="unclaimed"
    )

    image = models.ImageField(
        upload_to='item_images/',
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_name} ({self.item_type}) - {self.status}"
