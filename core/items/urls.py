from django.urls import path
from .views import report_lost_item, report_found_item,list_lost_items,list_found_items,search_items,delete_item,my_lost_items,found_from_lost,pending_matches,approve_match,reject_match

urlpatterns = [
    path('report-lost/', report_lost_item, name='report_lost'),
    path('report-found/', report_found_item, name='report_found'),
    path('lost/', list_lost_items, name='list_lost_items'),
    path('found/', list_found_items, name='list_found_items'),
    path('search/', search_items, name='search_items'),
    path('delete/<int:item_id>/', delete_item, name='delete_item'),
    path('my-lost/',my_lost_items, name='my_lost_items'),
    path('found-from-lost/<int:item_id>/', found_from_lost, name='found_from_lost'),
    path("pending-matches/", pending_matches, name="pending_matches"),
    path("approve-match/<int:item_id>/", approve_match, name="approve_match"),
    path("reject-match/<int:item_id>/", reject_match, name="reject_match"),


]   
