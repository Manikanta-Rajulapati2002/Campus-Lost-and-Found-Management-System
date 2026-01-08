from django.urls import path
from .views import ai_search_view

urlpatterns = [
    path('ai-search/', ai_search_view, name='ai_search'),
]
