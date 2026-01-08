from django.contrib import admin
from .models import Claim


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'item', 'claimed_by', 'status',
        'created_at', 'reviewed_by', 'reviewed_at'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('item__item_name', 'claimed_by__username', 'message')
