from django.contrib import admin
from .models import Item

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('item_name','item_type','category','color','location',
                    'status','reported_by','date_reported')
    list_filter = ('item_type','category','status','location')
    search_fields = ('item_name','description','location','reported_by_username')
